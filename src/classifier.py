"""
Ticket classifier: assigns/validates category and severity from the
raw description text. In this demo it's rule/keyword-based so it runs
with zero dependencies -- but it's structured so you can swap in a
real ML model (e.g. TF-IDF + LogisticRegression, or a small transformer)
without touching the calling code. See `classify_with_ml_stub()` below
for where that would plug in.

In a client engagement, this is the "ticket analytics" / auto-tagging
layer that reduces manual triage effort before automation even kicks in.
"""
import re

CATEGORY_KEYWORDS = {
    "disk_space": ["disk usage", "low space", "disk full"],
    "service_down": ["not responding", "service down", "service '"],
    "password_reset": ["password reset", "locked out"],
    "job_failure": ["batch job", "exit code", "job failed"],
    "memory_leak": ["memory utilization", "high memory"],
    "login_failure": ["failed login", "account may be locked"],
    "certificate_expiry": ["ssl certificate", "certificate for"],
    "network_latency": ["latency", "increased latency"],
    "queue_backlog": ["message queue", "backlog exceeds"],
    "license_expiry": ["license for", "license expiring"],
}

SEVERITY_RULES = {
    "P1": ["not responding", "service down", "outage"],
    "P2": ["low space", "high memory", "batch job", "backlog exceeds", "certificate"],
    "P3": ["password reset", "locked out", "latency", "failed login"],
    "P4": ["license"],
}


def classify_ticket(description: str):
    """Returns (category, severity, confidence) for a raw ticket description."""
    text = description.lower()

    category = "uncategorized"
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            category = cat
            break

    severity = "P3"  # default
    for sev, keywords in SEVERITY_RULES.items():
        if any(kw in text for kw in keywords):
            severity = sev
            break

    # crude confidence signal: more keyword hits = more confident
    hits = sum(1 for kws in CATEGORY_KEYWORDS.values() for kw in kws if kw in text)
    confidence = min(0.6 + 0.1 * hits, 0.99)

    return category, severity, round(confidence, 2)


def classify_with_ml_stub(description: str):
    """
    Placeholder for a real ML classifier.
    Swap-in plan (documented in README):
      1. Label ~500 historical tickets with category/severity.
      2. Vectorize with TF-IDF.
      3. Train a LogisticRegression / small XGBoost classifier.
      4. Replace the call to classify_ticket() in main.py with this function.
    """
    raise NotImplementedError("ML classifier not trained in this demo -- see docstring.")


if __name__ == "__main__":
    samples = [
        "Disk usage on server APP-SVR-512 at 91%, low space warning",
        "Service 'OrderProcessingSvc' on host 231 is not responding",
        "User user482@company.com locked out, requesting password reset",
    ]
    for s in samples:
        print(s, "->", classify_ticket(s))
