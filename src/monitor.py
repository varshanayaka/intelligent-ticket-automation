"""
Self-healing / preventive monitoring simulation.

This directly implements the JD phrase "automated monitoring, preventive
monitoring, predictive monitoring, self-healing" -- the idea being that
some issues never need to become a ticket at all if caught early.

Simulates polling system metrics (disk usage, CPU) every "tick".
  - value crosses WARNING threshold  -> auto-heal attempt (e.g. clear cache)
  - value crosses CRITICAL threshold -> create a real ticket (couldn't self-heal)
  - otherwise -> log a clean reading, no action

In production this would be a scheduled bot (cron / AA schedule) polling
real metrics via SNMP, a monitoring API (Datadog/Nagios/SolarWinds), or
custom agents on the app servers.
"""
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.db import get_connection, init_db, DB_BACKEND

PLACEHOLDER = "%s" if DB_BACKEND == "mysql" else "?"

METRICS = {
    "disk_usage":     {"warning": 80, "critical": 95, "unit": "%"},
    "cpu_usage":       {"warning": 75, "critical": 90, "unit": "%"},
}


def simulate_reading(metric):
    """Simulate a metric reading -- mostly healthy, occasionally elevated."""
    roll = random.random()
    if roll < 0.7:
        return random.uniform(20, 60)   # healthy
    elif roll < 0.92:
        return random.uniform(60, 85)   # warning zone
    else:
        return random.uniform(85, 99)   # critical zone


def log_event(metric, value, threshold, action, linked_ticket_id=None):
    query = (f"INSERT INTO monitoring_events (detected_at, metric, value, threshold, "
              f"action_taken, linked_ticket_id) VALUES "
              f"({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, [datetime.now().isoformat(sep=" "), metric, round(value, 1),
                             threshold, action, linked_ticket_id])
        conn.commit()


def create_ticket_from_monitoring(metric, value):
    query = (f"INSERT INTO tickets (created_at, source, raw_description, category, "
              f"severity, status, sla_minutes) VALUES "
              f"({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})")
    category = "disk_space" if metric == "disk_usage" else "memory_leak"
    desc = f"[Auto-detected] {metric} reached {value:.1f}% -- exceeded critical threshold."
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, [datetime.now().isoformat(sep=" "), "monitoring", desc,
                             category, "P1", "open", 30])
        conn.commit()
        return cur.lastrowid


def run_monitoring_cycle(n_ticks=20):
    init_db()
    healed, tickets_created, clean = 0, 0, 0

    for _ in range(n_ticks):
        for metric, thresholds in METRICS.items():
            value = simulate_reading(metric)

            if value >= thresholds["critical"]:
                ticket_id = create_ticket_from_monitoring(metric, value)
                log_event(metric, value, thresholds["critical"], "ticket_created", ticket_id)
                tickets_created += 1
            elif value >= thresholds["warning"]:
                log_event(metric, value, thresholds["warning"], "self_healed")
                healed += 1
            else:
                log_event(metric, value, thresholds["warning"], "none")
                clean += 1

    print(f"Monitoring cycle complete: {clean} clean readings, "
          f"{healed} self-healed (prevented a ticket), "
          f"{tickets_created} escalated to a P1 ticket.")


if __name__ == "__main__":
    run_monitoring_cycle()
