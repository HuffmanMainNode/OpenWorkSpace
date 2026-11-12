"""Small explicit permission policy primitive. No implicit grants."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    permission: str


def authorize(required: tuple[str, ...] | list[str], granted: set[str] | frozenset[str]) -> list[PolicyDecision]:
    """Evaluate each requested permission against explicit grants (default deny)."""
    return [
        PolicyDecision(
            allowed=permission in granted,
            reason="explicit grant" if permission in granted else "no matching explicit grant",
            permission=permission,
        )
        for permission in required
    ]
