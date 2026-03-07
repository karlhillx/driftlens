from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _flatten(prefix: str, value: Any, out: dict[str, str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            nxt = f"{prefix}.{k}" if prefix else str(k)
            _flatten(nxt, v, out)
        return
    if isinstance(value, list):
        out[prefix] = json.dumps(value, sort_keys=True)
        return
    out[prefix] = "" if value is None else str(value)


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def load_yaml(path: Path) -> dict[str, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, str] = {}
    _flatten("", raw, out)
    return out


def load_json(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    _flatten("", raw, out)
    return out


def load_file(path: Path) -> dict[str, str]:
    name = path.name.lower()
    if name.endswith(".env") or name == ".env":
        return load_env(path)
    if name.endswith(".yaml") or name.endswith(".yml"):
        return load_yaml(path)
    if name.endswith(".json"):
        return load_json(path)
    return {}


def load_snapshot(root: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root))
        parsed = load_file(p)
        for k, v in parsed.items():
            data[f"{rel}:{k}"] = v
    return data
