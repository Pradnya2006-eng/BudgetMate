import re
import sqlite3
from datetime import date, timedelta

import pytest

from conftest import register

TODAY = date.today().isoformat()


def tx(**overrides):
    body = {
        "type": "expense",
        "amount": 250,
        "category": "Food",
        "description": "Lunch",
        "date": TODAY,
    }
    body.update(overrides)
    return body


# ---------------------------------------------------------------- accounts


def test_register_logs_you_in(client):
    res = register(client)
    assert res.status_code == 201
    assert res.get_json()["user"]["email"] == "priya@example.com"

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["name"] == "Priya Test"


def test_cookie_is_httponly_and_samesite(client):
    cookie = register(client).headers["Set-Cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_password_is_stored_hashed(client, db_path):
    register(client, password="secret1234")
    stored = sqlite3.connect(db_path).execute("SELECT password_hash FROM users").fetchone()[0]
    assert "secret1234" not in stored
    assert stored.startswith(("scrypt:", "pbkdf2:"))


def test_duplicate_email_is_rejected_case_insensitively(client, make_client):
    register(client, email="priya@example.com")
    res = register(make_client(), email="  PRIYA@Example.com ")
    assert res.status_code == 409
    assert "already exists" in res.get_json()["error"]


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"name": "", "email": "a@b.co", "password": "secret1234"}, "name"),
        ({"name": "A", "email": "not-an-email", "password": "secret1234"}, "valid email"),
        ({"name": "A", "email": "a@b.co", "password": "short"}, "at least 8"),
        ({"name": "A", "email": "a@b.co", "password": "x" * 200}, "at most"),
        ({"name": "A", "email": "a@b.co"}, "at least 8"),
    ],
)
def test_register_validation(client, payload, message):
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert message in res.get_json()["error"]


def test_login_and_logout(client, make_client):
    register(client)

    other = make_client()
    res = other.post(
        "/api/auth/login", json={"email": " PRIYA@example.com", "password": "secret1234"}
    )
    assert res.status_code == 200
    assert other.get("/api/auth/me").status_code == 200

    other.post("/api/auth/logout")
    assert other.get("/api/auth/me").status_code == 401


def test_wrong_password_and_unknown_email_look_identical(client, make_client):
    register(client)
    wrong = make_client().post(
        "/api/auth/login", json={"email": "priya@example.com", "password": "nope-nope-1"}
    )
    unknown = make_client().post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-1"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


def test_login_is_rate_limited(client):
    register(client)
    attempt = {"email": "priya@example.com", "password": "wrong-password"}
    for _ in range(10):
        assert client.post("/api/auth/login", json=attempt).status_code == 401
    assert client.post("/api/auth/login", json=attempt).status_code == 429
    # Even the right password is refused while the limit is active.
    good = {"email": "priya@example.com", "password": "secret1234"}
    assert client.post("/api/auth/login", json=good).status_code == 429


# ---------------------------------------------------------- password reset


def reset_token_from(mails):
    return re.search(r"reset_token=([\w-]+)", mails[-1][2]).group(1)


def test_forgot_password_flow(client, make_client, mails):
    register(client)

    res = make_client().post("/api/auth/forgot", json={"email": "priya@example.com"})
    assert res.status_code == 200
    assert len(mails) == 1
    to, name, link = mails[0]
    assert (to, name) == ("priya@example.com", "Priya Test")
    assert link.startswith("http://app.test/?reset_token=")

    token = reset_token_from(mails)
    browser = make_client()
    res = browser.post("/api/auth/reset", json={"token": token, "password": "brand-new-pass"})
    assert res.status_code == 200

    login = make_client()
    old = login.post("/api/auth/login", json={"email": "priya@example.com", "password": "secret1234"})
    new = login.post(
        "/api/auth/login", json={"email": "priya@example.com", "password": "brand-new-pass"}
    )
    assert old.status_code == 401
    assert new.status_code == 200


def test_unknown_email_gets_same_answer_and_no_email(client, mails):
    known = client.post("/api/auth/forgot", json={"email": "ghost@example.com"})
    assert known.status_code == 200
    assert known.get_json() == {"ok": True}
    assert mails == []


def test_forgot_rejects_malformed_email(client):
    assert client.post("/api/auth/forgot", json={"email": "nope"}).status_code == 400


def test_only_a_hash_of_the_token_is_stored(client, mails, db_path):
    register(client)
    client.post("/api/auth/forgot", json={"email": "priya@example.com"})
    token = reset_token_from(mails)
    stored = sqlite3.connect(db_path).execute("SELECT token_hash FROM password_resets").fetchone()[0]
    assert token not in stored
    assert len(stored) == 64


def test_reset_link_works_only_once(client, make_client, mails):
    register(client)
    client.post("/api/auth/forgot", json={"email": "priya@example.com"})
    token = reset_token_from(mails)

    first = client.post("/api/auth/reset", json={"token": token, "password": "first-new-pass"})
    second = client.post("/api/auth/reset", json={"token": token, "password": "second-new-pass"})
    assert first.status_code == 200
    assert second.status_code == 400
    assert "expired or was already used" in second.get_json()["error"]

    # The second attempt must not have changed the password.
    ok = make_client().post(
        "/api/auth/login", json={"email": "priya@example.com", "password": "first-new-pass"}
    )
    assert ok.status_code == 200


def test_expired_link_is_refused(client, mails, db_path):
    register(client)
    client.post("/api/auth/forgot", json={"email": "priya@example.com"})
    token = reset_token_from(mails)

    long_ago = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d 00:00:00")
    raw = sqlite3.connect(db_path)
    raw.execute("UPDATE password_resets SET expires_at = ?", (long_ago,))
    raw.commit()

    res = client.post("/api/auth/reset", json={"token": token, "password": "brand-new-pass"})
    assert res.status_code == 400


def test_fake_token_is_refused(client):
    register(client)
    res = client.post("/api/auth/reset", json={"token": "made-up", "password": "brand-new-pass"})
    assert res.status_code == 400


def test_weak_new_password_does_not_use_up_the_link(client, mails):
    register(client)
    client.post("/api/auth/forgot", json={"email": "priya@example.com"})
    token = reset_token_from(mails)

    weak = client.post("/api/auth/reset", json={"token": token, "password": "short"})
    assert weak.status_code == 400
    again = client.post("/api/auth/reset", json={"token": token, "password": "long-enough-1"})
    assert again.status_code == 200


def test_newer_reset_request_does_not_break_but_reset_invalidates_all(client, mails):
    register(client)
    client.post("/api/auth/forgot", json={"email": "priya@example.com"})
    old_token = reset_token_from(mails)
    client.post("/api/auth/forgot", json={"email": "priya@example.com"})
    new_token = reset_token_from(mails)
    assert old_token != new_token

    assert client.post(
        "/api/auth/reset", json={"token": new_token, "password": "brand-new-pass"}
    ).status_code == 200
    assert client.post(
        "/api/auth/reset", json={"token": old_token, "password": "another-pass-1"}
    ).status_code == 400


def test_forgot_is_rate_limited_without_revealing_it(client, mails):
    register(client)
    for _ in range(8):
        res = client.post("/api/auth/forgot", json={"email": "priya@example.com"})
        assert res.status_code == 200
    assert len(mails) == 5


def test_mail_failure_does_not_break_the_request(db_path, tmp_path):
    import sqlite_stand_in
    from budgetmate import create_app

    def broken_mailer(*args):
        raise RuntimeError("SMTP down")

    app = create_app(
        overrides={"SECRET_KEY": "k", "STATIC_DIR": str(tmp_path / "x")},
        db_factory=sqlite_stand_in.factory_for(db_path),
        mailer=broken_mailer,
    )
    client = app.test_client()
    register(client)
    assert client.post("/api/auth/forgot", json={"email": "priya@example.com"}).status_code == 200


# ------------------------------------------------------------ transactions


def test_transactions_need_login(client):
    assert client.get("/api/transactions").status_code == 401
    assert client.post("/api/transactions", json=tx()).status_code == 401
    assert client.delete("/api/transactions/1").status_code == 401
    assert client.get("/api/budget").status_code == 401
    assert client.put("/api/budget", json={"monthly_budget": 5}).status_code == 401


def test_add_and_list_transactions_newest_first(logged_in):
    logged_in.post("/api/transactions", json=tx(category="Rent", amount=4500, date="2026-10-01"))
    logged_in.post("/api/transactions", json=tx(category="Food", amount=1200.5, date="2026-10-20"))
    created = logged_in.post(
        "/api/transactions", json=tx(category="Bills", amount=300, date="2026-10-20")
    )
    assert created.status_code == 201
    assert created.get_json()["transaction"]["category"] == "Bills"

    items = logged_in.get("/api/transactions").get_json()["transactions"]
    assert [i["category"] for i in items] == ["Bills", "Food", "Rent"]  # same day: newest first
    assert items[1]["amount"] == 1200.5
    assert items[1]["date"] == "2026-10-20"
    assert set(items[0]) == {"id", "type", "amount", "category", "description", "date"}


def test_amount_is_rounded_to_paise(logged_in):
    res = logged_in.post("/api/transactions", json=tx(amount="10.005"))
    assert res.get_json()["transaction"]["amount"] == 10.01


@pytest.mark.parametrize(
    "override, message",
    [
        ({"amount": 0}, "greater than 0"),
        ({"amount": -5}, "greater than 0"),
        ({"amount": "abc"}, "valid amount"),
        ({"amount": True}, "valid amount"),
        ({"amount": None}, "valid amount"),
        ({"amount": "NaN"}, "valid amount"),
        ({"amount": 10**10}, "too large"),
        ({"type": "gift"}, "income or expense"),
        ({"category": ""}, "category"),
        ({"category": "x" * 61}, "too long"),
        ({"description": "x" * 81}, "80 characters"),
        ({"date": "28-10-2026"}, "valid date"),
        ({"date": "2026-02-30"}, "valid date"),
        ({"date": (date.today() + timedelta(days=5)).isoformat()}, "future"),
    ],
)
def test_transaction_validation(logged_in, override, message):
    res = logged_in.post("/api/transactions", json=tx(**override))
    assert res.status_code == 400
    assert message in res.get_json()["error"]
    assert logged_in.get("/api/transactions").get_json()["transactions"] == []


def test_delete_transaction(logged_in):
    new_id = logged_in.post("/api/transactions", json=tx()).get_json()["transaction"]["id"]
    assert logged_in.delete(f"/api/transactions/{new_id}").status_code == 200
    assert logged_in.get("/api/transactions").get_json()["transactions"] == []
    assert logged_in.delete(f"/api/transactions/{new_id}").status_code == 404


def test_people_cannot_see_or_delete_each_others_data(client, make_client):
    register(client, email="a@example.com")
    a_id = client.post("/api/transactions", json=tx(category="Secret")).get_json()["transaction"]["id"]
    client.put("/api/budget", json={"monthly_budget": 9999})

    other = make_client()
    register(other, email="b@example.com", name="Bee")
    assert other.get("/api/transactions").get_json()["transactions"] == []
    assert other.get("/api/budget").get_json()["monthly_budget"] == 0
    assert other.delete(f"/api/transactions/{a_id}").status_code == 404

    # ...and A's data is still there.
    assert len(client.get("/api/transactions").get_json()["transactions"]) == 1


def test_deleting_a_user_removes_their_rows(client, db_path):
    register(client)
    client.post("/api/transactions", json=tx())
    client.put("/api/budget", json={"monthly_budget": 100})

    raw = sqlite3.connect(db_path)
    raw.execute("PRAGMA foreign_keys = ON")
    raw.execute("DELETE FROM users")
    raw.commit()
    for table in ("transactions", "budgets"):
        assert raw.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


# ------------------------------------------------------------------ budget


def test_budget_defaults_to_zero_and_can_be_changed_twice(logged_in):
    assert logged_in.get("/api/budget").get_json() == {"monthly_budget": 0}
    assert logged_in.put("/api/budget", json={"monthly_budget": 5000}).status_code == 200
    assert logged_in.get("/api/budget").get_json()["monthly_budget"] == 5000
    assert logged_in.put("/api/budget", json={"monthly_budget": "7500.5"}).status_code == 200
    assert logged_in.get("/api/budget").get_json()["monthly_budget"] == 7500.5
    assert logged_in.put("/api/budget", json={"monthly_budget": 0}).status_code == 200
    assert logged_in.get("/api/budget").get_json()["monthly_budget"] == 0


@pytest.mark.parametrize("value", [-1, "x", None, True, 10**10])
def test_budget_validation(logged_in, value):
    assert logged_in.put("/api/budget", json={"monthly_budget": value}).status_code == 400


# ------------------------------------------------------------ app behaviour


def test_non_json_bodies_get_a_json_error(client):
    res = client.post(
        "/api/auth/login", data="email=a&password=b", content_type="text/plain"
    )
    assert res.status_code == 415
    assert "error" in res.get_json()


def test_json_that_is_not_an_object_is_rejected(client):
    assert client.post("/api/auth/login", json=["a", "b"]).status_code == 400


def test_unknown_api_route_is_json_404(client):
    res = client.get("/api/nothing-here")
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_health_check(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_security_headers_and_no_caching_of_api(logged_in):
    res = logged_in.get("/api/transactions")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Cache-Control"] == "no-store"


def test_database_problems_become_helpful_messages(tmp_path):
    from budgetmate import create_app

    class OperationalError(Exception):
        pass

    def refuse():
        raise OperationalError(2003, "Can't connect")

    app = create_app(
        overrides={"SECRET_KEY": "k", "STATIC_DIR": str(tmp_path / "x")}, db_factory=refuse
    )
    res = app.test_client().get("/api/health")
    assert res.status_code == 503
    assert "Is the MySQL server running" in res.get_json()["error"]


def test_unexpected_errors_do_not_leak_details(tmp_path):
    from budgetmate import create_app

    def boom():
        raise RuntimeError("secret internals")

    app = create_app(
        overrides={"SECRET_KEY": "k", "STATIC_DIR": str(tmp_path / "x")}, db_factory=boom
    )
    res = app.test_client().get("/api/health")
    assert res.status_code == 500
    assert "secret internals" not in res.get_data(as_text=True)


# ------------------------------------------------------- serving the React app


@pytest.fixture
def built_app(db_path, tmp_path):
    import sqlite_stand_in
    from budgetmate import create_app

    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>BudgetMate</title>")
    (dist / "assets" / "app.js").write_text("console.log('hi')")
    (tmp_path / "secret.txt").write_text("top secret")

    return create_app(
        overrides={"SECRET_KEY": "k", "STATIC_DIR": str(dist)},
        db_factory=sqlite_stand_in.factory_for(db_path),
    )


def test_built_frontend_is_served(built_app):
    client = built_app.test_client()
    assert b"BudgetMate" in client.get("/").data
    assert client.get("/assets/app.js").data == b"console.log('hi')"
    assert b"BudgetMate" in client.get("/some/page").data  # React handles its own routes


def test_built_frontend_does_not_swallow_api_or_leak_files(built_app):
    client = built_app.test_client()
    missing = client.get("/api/nothing-here")
    assert missing.status_code == 404
    assert missing.is_json

    for sneaky in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        assert b"top secret" not in client.get(sneaky).data
