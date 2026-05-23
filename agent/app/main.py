"""Entry helpers for the ContextGuard local agent."""

from agent.app import __version__


def get_app_metadata() -> dict[str, str]:
    """Return basic metadata used by smoke tests and future health checks."""
    return {
        "name": "ContextGuard Local Agent",
        "status": "ready",
        "version": __version__,
    }

