"""
Orchestrator: the "brain" that ties classification + automation bots
+ escalation together. This is the piece that would map to an
Automation Anywhere Control Room workflow / bot trigger schedule
in a production deployment.

Flow per open ticket:
  1. Classify (category, severity) if not already set.
  2. Find a bot whose can_handle() matches the category.
  3. Run the bot.
  4. success  -> mark ticket auto_resolved, compute MTTR.
  5. failed/none -> mark ticket escalated (goes to human queue).
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.db import get_connection, init_db, DB_BACKEND
from src.classifier import classify_ticket
from src.bots.disk_cleanup_bot import DiskCleanupBot
from src.bots.service_restart_bot import ServiceRestartBot
from src.bots.password_reset_bot import PasswordResetBot

BOTS = [DiskCleanupBot(), ServiceRestartBot(), PasswordResetBot()]
PLACEHOLDER = "%s" if DB_BACKEND == "mysql" else "?"


def fetch_open_tickets():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tickets WHERE status = 'open'")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]


def update_ticket(ticket_id, **fields):
    set_clause = ", ".join(f"{k} = {PLACEHOLDER}" for k in fields)
    query = f"UPDATE tickets SET {set_clause} WHERE ticket_id = {PLACEHOLDER}"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, list(fields.values()) + [ticket_id])
        conn.commit()


def log_bot_run(ticket_id, run):
    query = (f"INSERT INTO bot_runs (ticket_id, bot_name, started_at, finished_at, outcome, log) "
              f"VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, [ticket_id, run["bot_name"], run["started_at"],
                             run["finished_at"], run["outcome"], run["log"]])
        conn.commit()


def process_ticket(ticket):
    ticket_id = ticket["ticket_id"]

    # 1. Classify if missing/uncategorized
    if not ticket.get("category"):
        category, severity, _conf = classify_ticket(ticket["raw_description"])
        update_ticket(ticket_id, category=category, severity=severity)
        ticket["category"] = category
        ticket["severity"] = severity

    # 2 & 3. Find and run a matching bot
    matched_bot = next((b for b in BOTS if b.can_handle(ticket)), None)
    if matched_bot is None:
        update_ticket(ticket_id, status="escalated", resolution_type="manual",
                       resolved_by="human_agent")
        print(f"Ticket {ticket_id} [{ticket['category']}] -> no bot available, escalated.")
        return

    run = matched_bot.run(ticket)
    log_bot_run(ticket_id, run)

    resolved_at = datetime.now().isoformat(sep=" ")
    created_at = datetime.fromisoformat(ticket["created_at"])
    mttr = (datetime.now() - created_at).total_seconds() / 60.0

    if run["outcome"] == "success":
        update_ticket(ticket_id, status="auto_resolved", resolved_at=resolved_at,
                       resolution_type="bot_auto", resolved_by=matched_bot.name,
                       mttr_minutes=round(mttr, 1))
        print(f"Ticket {ticket_id} [{ticket['category']}] -> resolved by {matched_bot.name}.")
    else:
        update_ticket(ticket_id, status="escalated", resolved_at=resolved_at,
                       resolution_type="manual", resolved_by="human_agent",
                       mttr_minutes=round(mttr, 1))
        print(f"Ticket {ticket_id} [{ticket['category']}] -> bot failed, escalated to human.")


def run_pipeline():
    init_db()
    tickets = fetch_open_tickets()
    print(f"Processing {len(tickets)} open tickets...\n")
    for t in tickets:
        process_ticket(t)
    print("\nDone. Run the dashboard (dashboard/app.py) to see the results.")


if __name__ == "__main__":
    run_pipeline()
