# DriftLens

**DriftLens is a CI-ready configuration drift gate for engineering teams.**

It compares environment snapshots (dev/stage/prod), classifies drift by risk, redacts sensitive output by default, and can fail pipelines when risk exceeds your threshold.

---

## Product features (v0.2)

- **Multi-format snapshot ingestion**: `.env`, `.yaml/.yml`, `.json`
- **Risk scoring**: `critical | high | medium | low`
- **Policy-as-code** via `.driftlens.yaml`
  - ignore keys/patterns
  - severity overrides
  - owner overrides (routing)
- **Owner routing + source pointers** on every finding (`owner`, `source_ref`)
- **Safe-by-default output**: values redacted unless `--show-values`
- **CI gating**: `--fail-on <severity>` with non-zero exit code
- **Reporting**: table, markdown, JSON, and **JUnit XML** (`--junit-out`)

---

## Quick start

```bash
cd driftlens
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Basic scan
driftlens scan --baseline ./configs/stage --target ./configs/prod

# CI gate: fail on high or above
driftlens scan --baseline ./configs/stage --target ./configs/prod --fail-on high

# Markdown report
driftlens scan --baseline ./configs/stage --target ./configs/prod --format markdown

# JSON report
driftlens scan --baseline ./configs/stage --target ./configs/prod --format json

# JUnit output for CI systems
driftlens scan --baseline ./configs/stage --target ./configs/prod --fail-on medium --junit-out ./artifacts/driftlens.xml
```

> Exit code behavior: DriftLens exits with code `2` when any item meets/exceeds `--fail-on`.

---

## Policy as code

DriftLens auto-loads `.driftlens.yaml` from target (then baseline), or use `--policy`.

Example policy:

```yaml
ignore_keys:
  - "service.yaml:build.timestamp"
  - "app.yaml:metadata.commit_sha"
severity_overrides:
  "service.yaml:api.base_url": high
  ".env:JWT_SECRET": critical
owner_overrides:
  "service.yaml:api.*": platform-team
  "service.yaml:queue.*": platform-team
  ".env:JWT_SECRET": security-team
```

Pattern matching supports exact match and prefix wildcard (`*`), e.g.:

- `"service.yaml:api.*"`

---

## Output modes

- `--format table` (default)
- `--format markdown`
- `--format json`
- `--junit-out path.xml` (for CI test report ingestion)

Findings include `owner` and `source_ref` so drift can be routed directly to the right team and file path.

By default, values are redacted:

- Baseline value: `[REDACTED]`
- Target value: `[REDACTED]`

Use `--show-values` only in trusted local contexts.

---

## CI examples

### GitHub Actions

```yaml
- name: DriftLens
  run: |
    driftlens scan \
      --baseline ./configs/stage \
      --target ./configs/prod \
      --fail-on high \
      --junit-out ./artifacts/driftlens.xml
```

### Bitbucket Pipelines

```yaml
- step:
    name: DriftLens Drift Gate
    script:
      - driftlens scan --baseline ./configs/stage --target ./configs/prod --fail-on high --junit-out ./artifacts/driftlens.xml
```

---

## Architecture

- `loaders.py` → parse/flatten config snapshots
- `engine.py` → compare snapshots + apply policy + score risk
- `policy.py` → policy loading, ignore rules, severity overrides
- `reporting.py` → redaction, threshold evaluation, JUnit rendering
- `cli.py` → user workflows and CI behavior

---

## Local example data

Use `examples/stage` and `examples/prod` for a quick smoke run:

```bash
driftlens scan --baseline ./examples/stage --target ./examples/prod --policy ./examples/.driftlens.yaml
```
