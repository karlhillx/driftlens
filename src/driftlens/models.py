from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DriftItem(BaseModel):
    key: str
    baseline_value: str | None
    target_value: str | None
    change_type: str  # added|removed|changed
    severity: Severity
    recommendation: str


class ScanResult(BaseModel):
    baseline: str
    target: str
    total: int
    by_severity: dict[str, int]
    items: list[DriftItem]
