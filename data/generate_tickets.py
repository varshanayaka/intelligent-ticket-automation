"""
Generates realistic synthetic IT support tickets to simulate an
Application Maintenance (AM) queue. Run this to populate the DB
with sample data before running the classifier / bots / dashboard.
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.db import get_connection, init_db, DB_BACKEND

TICKET_TEMPLATES = [
    ("disk_space", "P2", "Disk usage on server APP-SVR-{n} at {pct}%, low space warning"),
    ("service_down", "P1", "Service 'OrderProcessingSvc' on host {n} is not responding"),
    ("password_reset", "P3", "User user{n}@company.com locked out, requesting password reset"),
    ("job_failure", "P2", "Nightly batch job BATCH_{n} failed with exit code 1"),
    ("memory_leak", "P2", "High memory utilization ({pct}%) detected on app server {n}"),
    ("login_failure", "P3", "Multiple failed login attempts for user{n}, account may be locked"),
    ("certificate_expiry", "P2", "SSL certificate for app{n}.internal.company.com expires in 3 days"),
    ("network_latency", "P3", "Increased latency ({pct}ms) reported between APP-{n} and DB tier"),
    ("queue_backlog", "P2", "Message queue MQ_{n} backlog exceeds threshold (5000+ messages)"),
    ("license_expiry", "P4", "Software license for tool{n} expiring in 7 days"),
]

SOURCES = ["monitoring", "user_reported", "monitoring", "user_reported", "monitoring"]


def generate_tickets(n=150, days_back=30, seed=42):
    random.seed(seed)
    init_db()
    now = datetime.now()

    rows = []
    for _ in range(n):
        category, severity, template = random.choice(TICKET_TEMPLATES)
        n_val = random.randint(100, 999)
        pct_val = random.randint(70, 99)
        description = template.format(n=n_val, pct=pct_val)
        created_at = now - timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        source = random.choice(SOURCES)
        sla_map = {"P1": 30, "P2": 120, "P3": 480, "P4": 1440}  # minutes

        rows.append((
            created_at.isoformat(sep=" "),
            source,
            description,
            category,
            severity,
            "open",
            sla_map[severity],
        ))

    placeholder = "%s" if DB_BACKEND == "mysql" else "?"
    cols = "created_at, source, raw_description, category, severity, status, sla_minutes"
    query = f"INSERT INTO tickets ({cols}) VALUES ({', '.join([placeholder]*7)})"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(query, rows)
        conn.commit()

    print(f"Inserted {len(rows)} synthetic tickets.")


if __name__ == "__main__":
    generate_tickets()
