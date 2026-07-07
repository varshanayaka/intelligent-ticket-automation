import re
from src.bots.base_bot import BaseBot


class PasswordResetBot(BaseBot):
    """
    Simulates: generating a temporary password, updating the user record,
    and emailing the reset link -- a classic "assisted ticket resolution"
    case since it usually needs a final human confirmation step for
    security-sensitive changes.

    Real-world AA equivalent: Database package (UPDATE users SET
    temp_password=... WHERE email=...) + Email package to notify the user.
    This is intentionally modeled as MySQL-backed, since the JD calls
    out MySQL explicitly.
    """
    name = "password_reset_bot"

    def can_handle(self, ticket: dict) -> bool:
        return ticket.get("category") in ("password_reset", "login_failure")

    def resolve(self, ticket: dict) -> dict:
        match = re.search(r"user\d+@[\w.]+", ticket.get("raw_description", ""))
        user = match.group(0) if match else "unknown_user"
        return {
            "outcome": "success",
            "log": (f"Generated temporary password for {user}, updated user record, "
                     f"sent reset email. Flagged for user confirmation (assisted resolution)."),
        }
