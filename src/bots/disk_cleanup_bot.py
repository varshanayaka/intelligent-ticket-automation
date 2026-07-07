import random
from src.bots.base_bot import BaseBot


class DiskCleanupBot(BaseBot):
    """
    Simulates: clearing temp files / rotating logs / purging old backups
    when a disk_space ticket comes in.

    Real-world AA equivalent: File System package (delete files matching
    pattern *.tmp, *.log older than N days) + Run Command package to
    report freed space back into the ticket.
    """
    name = "disk_cleanup_bot"

    def can_handle(self, ticket: dict) -> bool:
        return ticket.get("category") == "disk_space"

    def resolve(self, ticket: dict) -> dict:
        # Simulate: 85% of the time cleanup frees enough space; else escalate
        success = random.random() < 0.85
        if success:
            freed_gb = round(random.uniform(2.0, 15.0), 1)
            return {
                "outcome": "success",
                "log": (f"Cleared temp files and rotated logs, freed {freed_gb}GB. "
                        f"Disk usage back under threshold."),
            }
        return {
            "outcome": "failed",
            "log": "Cleanup freed insufficient space -- likely a runaway process. Escalating to human agent.",
        }
