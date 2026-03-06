from __future__ import annotations

from .models import DriftItem, ScanResult
from .policy import DriftPolicy, owner_for_key, override_severity, should_ignore
from .scoring import classify_key, recommendation


def _split_source(key: str) -> tuple[str, str]:
    if ":" in key:
        source_file, source_key = key.split(":", 1)
        return source_file, source_key
    return "unknown", key


def compare_snapshots(
    baseline_name: str,
    target_name: str,
    baseline: dict[str, str],
    target: dict[str, str],
    policy: DriftPolicy | None = None,
) -> ScanResult:
    active_policy = policy or DriftPolicy()

    keys = sorted(set(baseline) | set(target))
    items: list[DriftItem] = []

    for key in keys:
        if should_ignore(key, active_policy):
            continue

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

        sev = override_severity(key, active_policy) or classify_key(key)
        source_file, source_key = _split_source(key)
        owner = owner_for_key(key, active_policy)
        items.append(
            DriftItem(
                key=key,
                source_file=source_file,
                source_key=source_key,
                source_ref=f"{source_file}:{source_key}",
                owner=owner,
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
