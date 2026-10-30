"""Transactions and monthly budget routes. All of them need a logged-in user,
and every query is limited to that user's own rows."""

from flask import Blueprint, g, jsonify

from .auth import error, json_body, login_required
from .db import commit, execute, query_all, query_one
from .validation import ValidationError, clean_transaction, money

bp = Blueprint("data", __name__, url_prefix="/api")


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def transaction_json(row):
    return {
        "id": row["id"],
        "type": row["type"],
        "amount": float(row["amount"]),
        "category": row["category"],
        "description": row["description"] or "",
        "date": _iso(row["tx_date"]),
    }


COLUMNS = "id, type, amount, category, description, tx_date"


@bp.get("/transactions")
@login_required
def list_transactions():
    rows = query_all(
        f"SELECT {COLUMNS} FROM transactions WHERE user_id = %s "
        "ORDER BY tx_date DESC, id DESC",
        (g.user["id"],),
    )
    return jsonify({"transactions": [transaction_json(row) for row in rows]})


@bp.post("/transactions")
@login_required
def add_transaction():
    try:
        fields = clean_transaction(json_body())
    except ValidationError as problem:
        return error(str(problem), 400)

    new_id, _ = execute(
        "INSERT INTO transactions (user_id, type, amount, category, description, tx_date) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            g.user["id"],
            fields["type"],
            str(fields["amount"]),
            fields["category"],
            fields["description"],
            fields["date"],
        ),
    )
    commit()

    row = query_one(
        f"SELECT {COLUMNS} FROM transactions WHERE id = %s AND user_id = %s",
        (new_id, g.user["id"]),
    )
    return jsonify({"transaction": transaction_json(row)}), 201


@bp.delete("/transactions/<int:transaction_id>")
@login_required
def delete_transaction(transaction_id):
    _, deleted = execute(
        "DELETE FROM transactions WHERE id = %s AND user_id = %s",
        (transaction_id, g.user["id"]),
    )
    commit()
    if deleted == 0:
        return error("That transaction doesn't exist.", 404)
    return jsonify({"ok": True})


@bp.get("/budget")
@login_required
def get_budget():
    row = query_one(
        "SELECT monthly_budget FROM budgets WHERE user_id = %s", (g.user["id"],)
    )
    return jsonify({"monthly_budget": float(row["monthly_budget"]) if row else 0})


@bp.put("/budget")
@login_required
def set_budget():
    try:
        amount = money(
            json_body().get("monthly_budget"), allow_zero=True, label="budget"
        )
    except ValidationError as problem:
        return error(str(problem), 400)

    if query_one("SELECT user_id FROM budgets WHERE user_id = %s", (g.user["id"],)):
        execute(
            "UPDATE budgets SET monthly_budget = %s WHERE user_id = %s",
            (str(amount), g.user["id"]),
        )
    else:
        execute(
            "INSERT INTO budgets (user_id, monthly_budget) VALUES (%s, %s)",
            (g.user["id"], str(amount)),
        )
    commit()
    return jsonify({"monthly_budget": float(amount)})

    # ---------------- ADMIN ROUTES ----------------

@bp.get("/admin/overview")
@login_required
def admin_overview():
    if g.user["role"] != "admin":
        return error("Admin access required.", 403)

    users = query_one("SELECT COUNT(*) AS total FROM users")
    transactions = query_one(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0)
                AS income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0)
                AS expenses
        FROM transactions
        """
    )

    return jsonify({
        "total_users": users["total"],
        "total_transactions": transactions["total"],
        "total_income": float(transactions["income"]),
        "total_expenses": float(transactions["expenses"])
    })


@bp.get("/admin/users")
@login_required
def admin_users():
    if g.user["role"] != "admin":
        return error("Admin access required.", 403)

    rows = query_all(
        """
        SELECT id, name, email, role, created_at
        FROM users
        ORDER BY id DESC
        """
    )

    return jsonify({
        "users": [
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "role": row["role"],
                "created_at": _iso(row["created_at"])
            }
            for row in rows
        ]
    })


@bp.get("/admin/transactions")
@login_required
def admin_transactions():
    if g.user["role"] != "admin":
        return error("Admin access required.", 403)

    rows = query_all(
        """
        SELECT
            t.id, t.type, t.amount, t.category,
            t.description, t.tx_date,
            u.name, u.email
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.tx_date DESC, t.id DESC
        """
    )

    return jsonify({
        "transactions": [
            {
                "id": row["id"],
                "type": row["type"],
                "amount": float(row["amount"]),
                "category": row["category"],
                "description": row["description"] or "",
                "date": _iso(row["tx_date"]),
                "user_name": row["name"],
                "user_email": row["email"]
            }
            for row in rows
        ]
    })
