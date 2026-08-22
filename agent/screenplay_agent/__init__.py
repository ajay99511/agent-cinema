"""Screenplay structural-map agent package.

Kept import-light on purpose: importing this package must NOT pull in the ADK / cloud stack,
so pure modules like `events` and `config` stay unit-testable without credentials.
Import the agent explicitly from `screenplay_agent.agent` when you need it.
"""

__all__ = ["config", "events"]
