from __future__ import annotations

from .models import DriftItem, ScanResult
from .scoring import classify_key, recommendation


def compare_snapshots(baseline_name: str, target_name: str, baseline: dict[str, str], target: dict[str, str]) -> ScanResult:
    keys = sorted(set(baseline) | set(target))
    items: list[DriftItem] = []

    for key in keys:
        b = baseline.get(key)
        t = target.get(key)
        if b == t:
            continue

        if b is None:
            change_type = "added"
        elif t is None:
            change_type = "removed"
        else:
            change_type = "changed"

        sev = classify_key(key)
        items.append(
            DriftItem(
                key=key,
                baseline_value=b,
                target_value=t,
                change_type=change_type,
                severity=sev,
                recommendation=recommendation(sev, key),
            )
        )

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda i: (order[i.severity.value], i.key))

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in items:
        counts[item.severity.value] += 1

    return ScanResult(
        baseline=baseline_name,
        target=target_name,
        total=len(items),
        by_severity=counts,
        items=items,
    )
