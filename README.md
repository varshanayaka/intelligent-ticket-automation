# Intelligent IT Ticket Automation System

A simulated **Application Maintenance (AM)** support desk that automatically classifies,
resolves, and reports on IT incidents — modeled on Accenture's "Intelligent Automation"
methodology for reducing ticket-based effort in AM projects.

> Built to demonstrate hands-on understanding of automation-driven incident management:
> ticket classification, RPA-style auto-resolution bots, preventive self-healing monitoring,
> and operational reporting (MTTR, automation rate, ticket trends).

## Why this project

This mirrors a real Application Maintenance automation stack:

| Requirement (job description) | Where it's implemented |
|---|---|
| Automation Anywhere / RPA-style bots | `src/bots/` — modular Task-Bot-style resolution bots |
| Incident management | `schema.sql`, `src/main.py` — full ticket lifecycle: open → auto_resolved / escalated |
| Ticket analytics | `src/classifier.py` — category + severity classification |
| Automated / preventive / predictive monitoring, self-healing | `src/monitor.py` |
| Automated service management & reporting | `dashboard/app.py` — MTTR, automation rate, trends |
| MySQL | `schema.sql` + `src/db.py` — dual SQLite/MySQL backend |
| Reducing ticket-based & non-ticket-based effort | Self-healing monitor prevents tickets before they're even created |

## Architecture

```
                 ┌─────────────────────┐
  Monitoring --> │  monitor.py          │ --(critical)--> creates ticket
  (CPU/Disk)     │  (self-healing /     │ --(warning)---> auto-heals, no ticket
                 │   preventive)        │
                 └─────────────────────┘
                            │
                            v
  User-reported   ┌─────────────────┐      ┌──────────────┐
  tickets ------> │   tickets table  │ ---> │ classifier.py │  (category, severity)
                  │  (MySQL/SQLite)  │      └──────────────┘
                  └─────────────────┘
                            │
                            v
                  ┌─────────────────────┐
                  │   main.py            │  orchestrator
                  │  (routes to bot)      │
                  └─────────────────────┘
                       │           │
             ┌─────────┘           └───────────┐
             v                                  v
   ┌───────────────────┐              ┌─────────────────┐
   │ Resolution bots     │  success -->│ ticket auto-      │
   │ - disk_cleanup_bot  │              │ resolved          │
   │ - service_restart    │  fail --->  │ escalated to human│
   │ - password_reset     │              └─────────────────┘
   └───────────────────┘
             │
             v
   ┌─────────────────────┐
   │ dashboard/app.py      │  Streamlit: MTTR, automation rate, trends
   └─────────────────────┘
```

## Quick start

```bash
git clone <this-repo>
cd intelligent-ticket-automation
pip install -r requirements.txt

# 1. Generate synthetic ticket data (150 tickets over 30 days)
python data/generate_tickets.py

# 2. Run a preventive monitoring cycle (self-healing before tickets are created)
python src/monitor.py

# 3. Run the automation pipeline (classify + auto-resolve + escalate)
python src/main.py

# 4. Launch the reporting dashboard
streamlit run dashboard/app.py
```

By default everything runs on **SQLite** (zero setup). To point at **MySQL** instead:

```bash
export DB_BACKEND=mysql
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=yourpassword
export MYSQL_DATABASE=ticket_automation
# then create the DB first: mysql -u root -p -e "CREATE DATABASE ticket_automation;"
python data/generate_tickets.py
```

No other code changes are needed — `src/db.py` handles both backends transparently.

## What each bot does

| Bot | Handles | Simulates |
|---|---|---|
| `disk_cleanup_bot` | disk_space | Clears temp files/logs, frees space |
| `service_restart_bot` | service_down, memory_leak | Restarts service, health-checks it |
| `password_reset_bot` | password_reset, login_failure | Generates temp password, updates user record (assisted resolution) |

Tickets with no matching bot (e.g. certificate renewals, license expiry) are correctly
routed to a human queue — not every ticket *should* be automated, and the system reflects that.

## Porting bots to real Automation Anywhere

Each bot in `src/bots/` documents its AA Community Edition equivalent in its docstring.
In short:
- `can_handle()` → a Decision node checking ticket category
- `resolve()` → the Task Bot's action sequence (File System / Service / Database packages)
- Escalation → a "Create Record" or notification action back to the ticket system

This was intentionally built in Python first so the *logic* is fully testable and
version-controlled, then wrapped as real AA bots for the parts that benefit from RPA
(desktop/file-system actions) — this mirrors how automation is actually piloted in AM
projects before being scaled into a full RPA platform.

## Results on synthetic data (150 tickets)

- ~35-40% automation rate (bot auto-resolves without human involvement)
- Preventive monitoring self-heals ~10% of potential issues before a ticket is ever created
- Full MTTR and category breakdowns available on the dashboard

## Tech stack

Python · SQLite/MySQL · Streamlit · Plotly · pandas · (Automation Anywhere Community Edition for bot porting)

## Possible extensions

- Swap `classifier.py`'s keyword rules for a trained ML model (TF-IDF + LogisticRegression) — stub included in `classify_with_ml_stub()`
- Add a Slack/Teams webhook for escalation notifications
- Add anomaly detection (e.g. isolation forest) to `monitor.py` for smarter predictive alerts
