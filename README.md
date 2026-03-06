# DriftLens

DriftLens detects risky configuration drift between environments (dev/stage/prod) across `.env`, YAML, and JSON files.

## Why

Subtle config differences cause expensive release failures. DriftLens compares two environment snapshots and ranks drift by risk.

## Quick start

```bash
cd driftlens
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# compare two folders
# e.g. ./configs/stage vs ./configs/prod
driftlens scan --baseline ./configs/stage --target ./configs/prod

# markdown output
driftlens scan --baseline ./configs/stage --target ./configs/prod --format markdown

# json output
driftlens scan --baseline ./configs/stage --target ./configs/prod --format json
```

## Risk model (MVP)

- **critical**: secret/auth/security keys changed or missing
- **high**: database/queue/host/endpoint style keys drift
- **medium**: feature/toggle/timeout/limit style keys drift
- **low**: everything else

## Supported formats

- `.env`
- `.yaml` / `.yml`
- `.json`

## Example

See `examples/` for sample stage/prod configs.
