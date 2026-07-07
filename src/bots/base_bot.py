"""
Base class for all resolution bots.

Design mirrors how you'd structure this in Automation Anywhere:
each bot is a discrete, single-purpose automation ("Task Bot") that:
  1. checks whether it CAN handle a given ticket (precondition)
  2. attempts a fix
  3. reports success / failure back to the orchestrator, which either
     closes the ticket (auto-resolved) or escalates to a human queue.

To port a bot to real Automation Anywhere Community Edition:
  - `can_handle()` becomes a Decision node reading the ticket category
  - `resolve()` becomes the Task Bot's action sequence
    (e.g. Run Command / File System package for disk cleanup,
    Service package for restarts, Database package for MySQL updates)
  - `escalate()` becomes a "Create Record" / notification action
"""
from abc import ABC, abstractmethod
from datetime import datetime


class BaseBot(ABC):
    name = "base_bot"

    @abstractmethod
    def can_handle(self, ticket: dict) -> bool:
        """Return True if this bot's category/preconditions match the ticket."""
        raise NotImplementedError

    @abstractmethod
    def resolve(self, ticket: dict) -> dict:
        """
        Attempt to resolve the ticket.
        Must return: {"outcome": "success"|"failed", "log": str}
        """
        raise NotImplementedError

    def run(self, ticket: dict) -> dict:
        started_at = datetime.now().isoformat(sep=" ")
        if not self.can_handle(ticket):
            return {
                "bot_name": self.name,
                "started_at": started_at,
                "finished_at": datetime.now().isoformat(sep=" "),
                "outcome": "skipped",
                "log": f"{self.name}: ticket category not handled by this bot.",
            }
        result = self.resolve(ticket)
        return {
            "bot_name": self.name,
            "started_at": started_at,
            "finished_at": datetime.now().isoformat(sep=" "),
            "outcome": result["outcome"],
            "log": result["log"],
        }
