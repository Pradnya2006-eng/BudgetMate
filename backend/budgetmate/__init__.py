"""BudgetMate backend: a Flask API on top of MySQL."""

import os

from flask import Flask, abort, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from . import auth, data
from .config import load_config
from .db import close_db, describe_connection_error, get_db, make_mysql_factory
from .mailer import send_reset_email
from .ratelimit import RateLimiter


def create_app(overrides=None, db_factory=None, mailer=None):
    """Builds the app. `db_factory` and `mailer` can be swapped out for tests."""
    config = load_config()
    config.update(overrides or {})

    app = Flask(__name__, static_folder=None)
    app.config.update(config)
    app.config.update(
        DB_FACTORY=db_factory or make_mysql_factory(config),
        MAILER=mailer or send_reset_email,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=config["SESSION_COOKIE_SECURE"],
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,  # stay logged in for 30 days
        MAX_CONTENT_LENGTH=64 * 1024,
    )

    # 10 wrong passwords per 15 minutes, and 5 reset requests per 15 minutes.
    app.extensions["login_limiter"] = RateLimiter(10, 15 * 60)
    app.extensions["forgot_limiter"] = RateLimiter(5, 15 * 60)

    app.teardown_appcontext(close_db)
    app.register_blueprint(auth.bp)
    app.register_blueprint(data.bp)

    @app.get("/api/health")
    def health():
        with get_db().cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify({"status": "ok"})

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        hint = describe_connection_error(exc)
        if hint:
            app.logger.error("Database problem: %s", exc)
            return jsonify({"error": hint}), 503
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Something went wrong on the server."}), 500

    @app.after_request
    def add_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if response.mimetype == "application/json":
            response.headers["Cache-Control"] = "no-store"
        return response

    _serve_built_frontend(app)
    return app


def _serve_built_frontend(app):
    """If `npm run build` has been run, serve the React app from Flask too, so
    the whole project runs as one server."""
    static_dir = app.config["STATIC_DIR"]
    if not os.path.isfile(os.path.join(static_dir, "index.html")):
        return

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path):
        if path.startswith("api/"):
            abort(404)
        full = os.path.join(static_dir, path)
        if path and os.path.isfile(full):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, "index.html")
