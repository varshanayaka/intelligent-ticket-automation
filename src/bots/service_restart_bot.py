import random
from src.bots.base_bot import BaseBot


class ServiceRestartBot(BaseBot):
    """
    Simulates: restarting an unresponsive service or a service with a
    memory leak, then health-checking it.

    Real-world AA equivalent: Service package (Stop/Start Service) +
    HTTP package to hit a health-check endpoint and confirm recovery.
    P1 tickets get one restart attempt before mandatory escalation --
    mirrors real SRE practice of not blindly retrying critical services.
    """
    name = "service_restart_bot"

    def can_handle(self, ticket: dict) -> bool:
        return ticket.get("category") in ("service_down", "memory_leak")

    def resolve(self, ticket: dict) -> dict:
        success = random.random() < 0.75
        if success:
            return {
                "outcome": "success",
                "log": "Service restarted successfully, health check passed on retry.",
            }
        return {
            "outcome": "failed",
            "log": ("Restart did not resolve the issue -- service failed health "
                     "check twice. Escalating to on-call engineer (P1 SLA)."),
        }
