from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .models import Severity


class DriftPolicy(BaseModel):
    ignore_keys: list[str] = Field(default_factory=list)
    severity_overrides: dict[str, Severity] = Field(default_factory=dict)


DEFAULT_POLICY_FILENAMES = (".driftlens.yaml", ".driftlens.yml")


def _matches(pattern: str, key: str) -> bool:
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return pattern == key


def should_ignore(key: str, policy: DriftPolicy) -> bool:
    return any(_matches(p, key) for p in policy.ignore_keys)


def override_severity(key: str, policy: DriftPolicy) -> Severity | None:
    for pattern, sev in policy.severity_overrides.items():
        if _matches(pattern, key):
            return sev
    return None


def load_policy(path: Path | None, baseline: Path, target: Path) -> DriftPolicy:
    candidates: list[Path] = []
    if path:
        candidates.append(path)
    else:
        for root in (target, baseline):
            for filename in DEFAULT_POLICY_FILENAMES:
                candidates.append(root / filename)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            raw = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            return DriftPolicy.model_validate(raw)

    return DriftPolicy()
