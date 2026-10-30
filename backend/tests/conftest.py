import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sqlite_stand_in  # noqa: E402
from budgetmate import create_app  # noqa: E402


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    sqlite_stand_in.create_database(path)
    return path


@pytest.fixture
def mails():
    """Every "email" the app tried to send: (to, name, link)."""
    return []


@pytest.fixture
def app(db_path, mails, tmp_path):
    return create_app(
        overrides={
            "SECRET_KEY": "test-secret",
            "FRONTEND_URL": "http://app.test",
            "STATIC_DIR": str(tmp_path / "no-build"),
        },
        db_factory=sqlite_stand_in.factory_for(db_path),
        mailer=lambda config, to, name, link: mails.append((to, name, link)),
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_client(app):
    """Extra browsers, for tests that need two people logged in at once."""
    return app.test_client


def register(client, email="priya@example.com", password="secret1234", name="Priya Test"):
    return client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )


@pytest.fixture
def logged_in(client):
    assert register(client).status_code == 201
    return client
