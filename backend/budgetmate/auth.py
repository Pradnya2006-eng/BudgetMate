"""Sign up, log in, log out and forgot-password routes."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, abort, current_app, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import commit, execute, is_duplicate_error, query_one
from .validation import (
    ValidationError,
    check_password,
    clean_email,
    clean_name,
    normalize_email,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Used to spend the same time checking a password for an unknown email, so
# response times don't reveal which emails have accounts.
_dummy_hash = None


def _get_dummy_hash():
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = generate_password_hash(secrets.token_hex(8))
    return _dummy_hash


def json_body():
    data = request.get_json()  # Flask answers 415/400 itself for non-JSON bodies
    if not isinstance(data, dict):
        abort(400, "Send a JSON object.")
    return data


def error(message, status):
    return jsonify({"error": message}), status


def public_user(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"]
    }


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _stamp(moment):
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def current_user():
    user_id = session.get("uid")
    if not user_id:
        return None
    return query_one("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            session.clear()
            return error("Please log in to continue.", 401)
        g.user = user
        return view(*args, **kwargs)

    return wrapped


def _start_session(user_id):
    session.clear()  # drop anything left from a previous login
    session["uid"] = user_id
    session.permanent = True


def _client_key(email):
    return f"{request.remote_addr}|{email}"


.post("/register")
def register():
    data = json_body()
    try:
        name = clean_name(data.get("name"))
        email = clean_email(data.get("email"))
        password = check_password(data.get("password"))
    except ValidationError as problem:
        return error(str(problem), 400)

    if query_one("SELECT id FROM users WHERE email = %s", (email,)):
        return error("An account with this email already exists.", 409)

    try:
        user_id, _ = execute(@bp
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, generate_password_hash(password)),
        )
        commit()
    except Exception as exc:  # two sign-ups with one email at the same moment
        if is_duplicate_error(exc):
            return error("An account with this email already exists.", 409)
        raise

    _start_session(user_id)
    return jsonify({"user": {"id": user_id, "name": name, "email": email}}), 201


@bp.post("/login")
def login():
    data = json_body()
    email = normalize_email(data.get("email"))
    password = data.get("password")

    if not email or not isinstance(password, str) or not password:
        return error("Please enter your email and password.", 400)

    limiter = current_app.extensions["login_limiter"]
    key = _client_key(email)
    if limiter.blocked(key):
        return error("Too many failed attempts. Please wait a few minutes and try again.", 429)

    row = query_one(
        "SELECT id, name, email, password_hash, role FROM users WHERE email = %s", (email,)
    )
    stored_hash = row["password_hash"] if row else _get_dummy_hash()
    password_ok = check_password_hash(stored_hash, password)

    if row is None or not password_ok:
        limiter.add(key)
        return error("Invalid email or password.", 401)

    limiter.reset(key)
    _start_session(row["id"])
    return jsonify({"user": public_user(row)})


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
def me():
    user = current_user()
    if user is None:
        session.clear()
        return error("Not logged in.", 401)
    return jsonify({"user": public_user(user)})


@bp.post("/forgot")
def forgot_password():
    """Always answers the same way, so it can't be used to find out which
    emails have accounts."""
    data = json_body()
    try:
        email = clean_email(data.get("email"))
    except ValidationError as problem:
        return error(str(problem), 400)

    reply = jsonify({"ok": True})

    limiter = current_app.extensions["forgot_limiter"]
    key = _client_key(email)
    if limiter.blocked(key):
        return reply
    limiter.add(key)

    user = query_one("SELECT id, name, email FROM users WHERE email = %s", (email,))
    if user is None:
        return reply

    config = current_app.config
    token = secrets.token_urlsafe(32)
    expires = utc_now() + timedelta(minutes=config["RESET_TOKEN_MINUTES"])
    execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
        (user["id"], _hash_token(token), _stamp(expires)),
    )
    commit()

    link = f"{config['FRONTEND_URL']}/?reset_token={token}"
    try:
        current_app.config["MAILER"](config, user["email"], user["name"], link)
    except Exception:
        # Still answer normally; the problem is for the server owner to fix.
        current_app.logger.exception("Could not send the password reset email")

    return reply


@bp.post("/reset")
def reset_password():
    data = json_body()
    token = data.get("token")

    try:
        password = check_password(data.get("password"))
    except ValidationError as problem:
        return error(str(problem), 400)  # checked first so a typo doesn't use up the link

    bad_link = "That link has expired or was already used. Please request a new one."
    if not isinstance(token, str) or not token:
        return error(bad_link, 400)

    now = _stamp(utc_now())
    row = query_one(
        "SELECT id, user_id FROM password_resets "
        "WHERE token_hash = %s AND used_at IS NULL AND expires_at > %s",
        (_hash_token(token), now),
    )
    if row is None:
        return error(bad_link, 400)

    # Mark the link used first. Only one request can win this update, so a
    # link can never be used twice, even if two requests arrive together.
    _, claimed = execute(
        "UPDATE password_resets SET used_at = %s WHERE id = %s AND used_at IS NULL",
        (now, row["id"]),
    )
    if claimed != 1:
        return error(bad_link, 400)

    execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (generate_password_hash(password), row["user_id"]),
    )
    # Any other links sent earlier stop working too.
    execute(
        "UPDATE password_resets SET used_at = %s WHERE user_id = %s AND used_at IS NULL",
        (now, row["user_id"]),
    )
    commit()

    session.clear()
    return jsonify({"ok": True})
