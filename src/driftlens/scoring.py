from __future__ import annotations

from .models import Severity

CRITICAL_MARKERS = ("secret", "token", "password", "api_key", "private_key", "auth", "oauth", "jwt")
HIGH_MARKERS = ("db", "database", "redis", "mongo", "queue", "broker", "host", "url", "endpoint")
MEDIUM_MARKERS = ("feature", "flag", "toggle", "timeout", "retry", "limit", "rate")


def classify_key(key: str) -> Severity:
    k = key.lower()
    if any(m in k for m in CRITICAL_MARKERS):
        return Severity.CRITICAL
    if any(m in k for m in HIGH_MARKERS):
        return Severity.HIGH
    if any(m in k for m in MEDIUM_MARKERS):
        return Severity.MEDIUM
    return Severity.LOW


def recommendation(sev: Severity, key: str) -> str:
    if sev == Severity.CRITICAL:
        return f"Validate secret handling for '{key}' immediately; rotate/reseal if unintended."
    if sev == Severity.HIGH:
        return f"Confirm connectivity/runtime impact for '{key}' before next deployment."
    if sev == Severity.MEDIUM:
        return f"Review behavior change risk for '{key}' and align across environments."
    return f"Review and normalize '{key}' when convenient."
