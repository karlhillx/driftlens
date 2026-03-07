from __future__ import annotations

from xml.sax.saxutils import escape

from .models import ScanResult, Severity


def redact_value(value: str | None, show_values: bool) -> str:
    if value is None:
        return "∅"
    if show_values:
        return value
    return "[REDACTED]"


def severity_ge(item: Severity, threshold: Severity) -> bool:
    order = {
        Severity.CRITICAL: 4,
        Severity.HIGH: 3,
        Severity.MEDIUM: 2,
        Severity.LOW: 1,
    }
    return order[item] >= order[threshold]


def to_junit_xml(result: ScanResult, fail_on: Severity) -> str:
    failures = [i for i in result.items if severity_ge(i.severity, fail_on)]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<testsuite name="driftlens" tests="{len(result.items)}" '
            f'failures="{len(failures)}">'
        ),
    ]

    for item in result.items:
        key = escape(item.key)
        change = escape(item.change_type)
        sev = item.severity.value
        lines.append(f'  <testcase classname="driftlens.{sev}" name="{key}:{change}">')
        if severity_ge(item.severity, fail_on):
            msg = escape(f"{sev} drift on {item.key}: {item.recommendation}")
            lines.append(f'    <failure message="{msg}"/>')
        lines.append("  </testcase>")

    lines.append("</testsuite>")
    return "\n".join(lines) + "\n"
