"""Sends the password-reset email."""

import smtplib
from email.message import EmailMessage


def send_reset_email(config, to_email, name, link):
    """Emails the reset link, or prints it when SMTP isn't configured.

    Printing keeps the forgot-password flow usable on a laptop with no mail
    account: copy the link from the terminal running the server.
    """
    minutes = config["RESET_TOKEN_MINUTES"]

    if not config["SMTP_HOST"]:
        print(
            "\n[BudgetMate] SMTP is not configured, so no email was sent.\n"
            f"[BudgetMate] Password reset link for {to_email} (valid {minutes} min):\n"
            f"[BudgetMate] {link}\n",
            flush=True,
        )
        return

    message = EmailMessage()
    message["Subject"] = "Reset your BudgetMate password"
    message["From"] = config["MAIL_FROM"]
    message["To"] = to_email
    message.set_content(
        f"Hi {name},\n\n"
        "Someone asked to reset the password for your BudgetMate account.\n"
        f"Open this link to choose a new one (it works for {minutes} minutes):\n\n"
        f"{link}\n\n"
        "If this wasn't you, you can ignore this email. Your password won't change.\n"
    )

    with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=15) as server:
        server.starttls()
        if config["SMTP_USER"]:
            server.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
        server.send_message(message)
