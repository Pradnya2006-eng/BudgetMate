"""Settings, read from environment variables (and backend/.env if present)."""

import os
import secrets
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except ImportError:  # python-dotenv is optional; real env vars still work
        return
    load_dotenv(BACKEND_DIR / ".env")


def _flag(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def load_config():
    _load_dotenv()

    secret = os.environ.get("SECRET_KEY", "").strip()
    if not secret:
        # Fine for a quick start, but everyone gets logged out on each restart.
        secret = secrets.token_hex(32)
        print(
            "WARNING: SECRET_KEY is not set in backend/.env, using a temporary one. "
            "Logins will reset whenever the server restarts.",
            flush=True,
        )

    return {
        "SECRET_KEY": secret,
        "DB_HOST": os.environ.get("DB_HOST", "localhost"),
        "DB_PORT": _int("DB_PORT", 3306),
        "DB_USER": os.environ.get("DB_USER", "root"),
        "DB_PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "DB_NAME": os.environ.get("DB_NAME", "budgetmate"),
        "FRONTEND_URL": os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/"),
        "SMTP_HOST": os.environ.get("SMTP_HOST", "").strip(),
        "SMTP_PORT": _int("SMTP_PORT", 587),
        "SMTP_USER": os.environ.get("SMTP_USER", "").strip(),
        "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
        "MAIL_FROM": os.environ.get("MAIL_FROM", "BudgetMate <no-reply@example.com>"),
        "RESET_TOKEN_MINUTES": _int("RESET_TOKEN_MINUTES", 60),
        # Where the built React app lives (created by `npm run build`).
        "STATIC_DIR": os.environ.get("STATIC_DIR", str(BACKEND_DIR.parent / "dist")),
        "SESSION_COOKIE_SECURE": _flag("COOKIE_SECURE"),
    }
