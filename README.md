# BudgetMate

A budgeting web app. Track income and expenses, set a monthly budget, and see where your money goes.

| Part | Technology |
| --- | --- |
| Frontend | React 19 + Vite |
| Backend | **Python (Flask)** REST API |
| Database | **MySQL** |

## Features

- Sign up, log in and log out, with passwords stored as salted hashes
- **Forgot password:** a reset link is emailed (or printed in the terminal during development), works once, and expires after an hour
- Each person only ever sees their own data
- Add income and expenses with a category, date and optional note
- Browse month by month
- Monthly budget with a progress bar and warnings as you near or pass it
- Spending breakdown by category
- Works on phones and desktops

## Run it on your computer

You need **Python 3.10+**, **Node.js 20+** and **MySQL 8.0.16+** (or MariaDB 10.5+).

### 1. Create the database

```bash
mysql -u root -p < backend/schema.sql
```

This creates a database called `budgetmate` with four tables (see below). You can also open `backend/schema.sql` in MySQL Workbench and run it.

### 2. Start the backend (Flask)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # Windows: copy .env.example .env
```

Open `backend/.env` and set `DB_PASSWORD` to your MySQL password and `SECRET_KEY` to a long random string (the file shows a command that makes one). Then:

```bash
python app.py
```

Check <http://127.0.0.1:5000/api/health>. It should show `{"status": "ok"}`. If it shows an error, the message says what to fix (wrong password, MySQL not running, schema not loaded).

### 3. Start the frontend (React)

In a second terminal, from the project folder:

```bash
npm install
npm run dev
```

Open <http://localhost:5173>. Vite forwards every `/api` request to Flask, so there is nothing else to configure.

### Forgot password during development

With `SMTP_HOST` empty in `backend/.env`, no email is sent. Instead, the reset link is printed in the terminal running Flask:

```
[BudgetMate] Password reset link for priya@example.com (valid 60 min):
[BudgetMate] http://localhost:5173/?reset_token=...
```

Open that link in the browser to choose a new password. To send real emails, fill in the `SMTP_*` values (for Gmail use `smtp.gmail.com`, port 587 and an [App Password](https://support.google.com/accounts/answer/185833)).

### Run it as a single server

```bash
npm run build          # creates dist/
cd backend
python app.py          # Flask now serves the React app too
```

Open <http://127.0.0.1:5000>. For a real deployment, run Flask with a production server such as `gunicorn "app:app"` (not `debug=True`), serve it over HTTPS, and set `COOKIE_SECURE=true`.

## Database design

```
users            (id, name, email UNIQUE, password_hash, created_at)
   │ 1
   ├──< transactions   (id, user_id FK, type, amount, category, description, tx_date)
   ├──1 budgets        (user_id PK/FK, monthly_budget)
   └──< password_resets (id, user_id FK, token_hash UNIQUE, expires_at, used_at)
```

All foreign keys use `ON DELETE CASCADE`, so deleting a user removes their data. Money is stored as `DECIMAL(12,2)`, never floating point.

## API

All paths start with `/api`. Bodies and responses are JSON. Errors look like `{"error": "message"}`.

| Method | Path | What it does | Login needed |
| --- | --- | --- | --- |
| POST | `/auth/register` | Create an account and log in | no |
| POST | `/auth/login` | Log in | no |
| POST | `/auth/logout` | Log out | no |
| GET | `/auth/me` | Who is logged in | yes |
| POST | `/auth/forgot` | Send a reset link | no |
| POST | `/auth/reset` | Set a new password using the link's token | no |
| GET | `/transactions` | List my transactions | yes |
| POST | `/transactions` | Add a transaction | yes |
| DELETE | `/transactions/<id>` | Delete one of mine | yes |
| GET | `/budget` | Get my monthly budget | yes |
| PUT | `/budget` | Set my monthly budget | yes |
| GET | `/health` | Check the server and database | no |

## Security notes

- Passwords are hashed with a per-password salt (Werkzeug's scrypt); the plain password is never stored or logged.
- Login uses a signed, `HttpOnly`, `SameSite=Lax` cookie, so scripts on the page can't read it.
- Every SQL query is parameterised, which prevents SQL injection.
- Every data query includes the logged-in `user_id`, so people can't reach each other's rows.
- Reset tokens are random, stored only as a hash, single-use and time-limited.
- Wrong-password attempts and reset requests are rate limited per address.
- The forgot-password endpoint gives the same answer whether or not an email has an account.

## Run the tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

The tests exercise every API route (accounts, password reset, transactions, budget, data isolation between users). They run against a small SQLite stand-in so they work without MySQL; the real database is created from `backend/schema.sql`.

## Project layout

```
backend/
  app.py                  starts the server
  schema.sql              MySQL tables
  requirements.txt        Python packages
  .env.example            settings template (copy to .env)
  budgetmate/
    __init__.py           builds the Flask app
    auth.py               register, login, forgot/reset password
    data.py               transactions and budget
    db.py                 MySQL connection helpers
    validation.py         input checks
    mailer.py             sends the reset email
    ratelimit.py          slows down password guessing
    config.py             reads settings
  tests/                  pytest tests
src/                      React app
  api/                    calls to the Flask API
  components/             screens and widgets
  hooks/  utils/
_original/                your first version, kept for reference
```
