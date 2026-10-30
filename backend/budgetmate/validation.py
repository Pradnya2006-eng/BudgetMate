"""Checks for incoming data. The React forms check the same rules, but the
server never trusts the browser, so everything is checked again here."""

import re
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128  # very long inputs make password hashing needlessly slow
MAX_AMOUNT = Decimal("1000000000")

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ValidationError(Exception):
    """Carries a message that is safe to show to the person using the app."""


def normalize_email(value):
    return value.strip().lower() if isinstance(value, str) else ""


def clean_email(value):
    email = normalize_email(value)
    if len(email) > 254 or not EMAIL_PATTERN.match(email):
        raise ValidationError("Please enter a valid email address.")
    return email


def clean_name(value):
    name = value.strip() if isinstance(value, str) else ""
    if not name:
        raise ValidationError("Please enter your name.")
    if len(name) > 100:
        raise ValidationError("That name is too long.")
    return name


def check_password(value):
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.")
    return value


def money(value, *, allow_zero=False, label="amount"):
    """Converts to a Decimal with 2 places, or raises ValidationError."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValidationError(f"Please enter a valid {label}.")
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        raise ValidationError(f"Please enter a valid {label}.") from None
    if not number.is_finite():
        raise ValidationError(f"Please enter a valid {label}.")

    number = number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if number < 0 or (number == 0 and not allow_zero):
        raise ValidationError(
            f"Enter a {label} of 0 or more." if allow_zero else f"Enter a {label} greater than 0."
        )
    if number > MAX_AMOUNT:
        raise ValidationError(f"That {label} looks too large.")
    return number


def clean_transaction(data):
    tx_type = data.get("type")
    if tx_type not in ("income", "expense"):
        raise ValidationError("Type must be income or expense.")

    amount = money(data.get("amount"))

    category = data.get("category")
    category = category.strip() if isinstance(category, str) else ""
    if not category:
        raise ValidationError("Please choose a category.")
    if len(category) > 60:
        raise ValidationError("That category name is too long.")

    description = data.get("description", "")
    description = description.strip() if isinstance(description, str) else ""
    if len(description) > 80:
        raise ValidationError("The note can be at most 80 characters.")

    raw_date = data.get("date")
    if not isinstance(raw_date, str) or not DATE_PATTERN.match(raw_date):
        raise ValidationError("Please choose a valid date.")
    try:
        tx_date = date.fromisoformat(raw_date)
    except ValueError:
        raise ValidationError("Please choose a valid date.") from None

    # The server's "today" can be a day behind the person's (time zones),
    # so allow one day of slack before calling a date "in the future".
    latest = datetime.now(timezone.utc).date() + timedelta(days=1)
    if tx_date > latest:
        raise ValidationError("The date can't be in the future.")

    return {
        "type": tx_type,
        "amount": amount,
        "category": category,
        "description": description,
        "date": tx_date.isoformat(),
    }
