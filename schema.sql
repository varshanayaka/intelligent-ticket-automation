-- Intelligent IT Ticket Automation System
-- Works on both MySQL and SQLite (minor type differences noted below)

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id       INTEGER PRIMARY KEY AUTOINCREMENT,  -- MySQL: use AUTO_INCREMENT
    created_at      TEXT NOT NULL,                       -- MySQL: DATETIME
    resolved_at     TEXT,                                -- MySQL: DATETIME
    source          TEXT NOT NULL,                       -- e.g. 'monitoring', 'user_reported'
    raw_description TEXT NOT NULL,
    category        TEXT,                                -- e.g. 'disk_space', 'service_down'
    severity        TEXT,                                -- 'P1','P2','P3','P4'
    status          TEXT NOT NULL DEFAULT 'open',         -- open, auto_resolved, escalated, closed
    resolution_type TEXT,                                 -- 'bot_auto', 'bot_assisted', 'manual'
    resolved_by     TEXT,                                 -- bot name or 'human_agent'
    sla_minutes     INTEGER,                              -- SLA target for this severity
    mttr_minutes    REAL                                  -- actual time to resolve
);

CREATE TABLE IF NOT EXISTS monitoring_events (
    event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at     TEXT NOT NULL,
    metric          TEXT NOT NULL,     -- 'disk_usage', 'cpu_usage', 'service_status'
    value           REAL,
    threshold       REAL,
    action_taken    TEXT,              -- 'self_healed', 'ticket_created', 'none'
    linked_ticket_id INTEGER,
    FOREIGN KEY (linked_ticket_id) REFERENCES tickets(ticket_id)
);

CREATE TABLE IF NOT EXISTS bot_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       INTEGER,
    bot_name        TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    outcome         TEXT,              -- 'success', 'failed', 'escalated'
    log             TEXT,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);
