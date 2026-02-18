import json
import re
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

# ------------------------------------------------------------
# REQUIRED FIELDS (multi-stack)
# ------------------------------------------------------------
required_fields = ("repository", "version")
for field in required_fields:
    if field not in data or str(data[field]).strip() == "":
        sys.exit(f"Missing required field: {field}")

repository = str(data["repository"]).strip()
version = str(data["version"]).strip()

# name pasa a ser opcional (solo display)
name = str(data.get("name") or repository).strip()


def slugify(value: str) -> str:
    """Convierte a un identificador seguro para nombres AWS (simple)."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9-_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def to_bool(v, default=False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y", "on"):
        return True
    if s in ("false", "0", "no", "n", "off"):
        return False
    return default

base = str(data.get("name") or repository).strip()

lambda_name = str(data.get("lambda_name") or base).strip()
state_machine_name = str(data.get("state_machine_name") or base).strip()
schedule_name = str(data.get("schedule_name") or base).strip()

# ------------------------------------------------------------
# Schedule (nuevo formato)
# ------------------------------------------------------------
schedule_obj = data.get("schedule") or {}
schedule_enabled = to_bool(schedule_obj.get("enabled"), default=True)

# Si no viene expression, usa default
schedule_expression = str(
    schedule_obj.get("expression")
    or data.get("schedule_expression")
    or "cron(0 10 * * ? *)"
).strip()

schedule_timezone = str(schedule_obj.get("timezone") or "America/Lima").strip()

# ------------------------------------------------------------
# Run after deploy (nuevo)
# ------------------------------------------------------------
run_after_deploy = to_bool(data.get("run_after_deploy"), default=False)

# Campos opcionales
description = str(data.get("description", "")).strip()

# ------------------------------------------------------------
# Outputs para GitHub Actions (GITHUB_OUTPUT)
# ------------------------------------------------------------
print(f"name={name}")
print(f"description={description}")
print(f"repository={repository}")
print(f"version={version}")

print(f"lambda_name={lambda_name}")
print(f"state_machine_name={state_machine_name}")
print(f"schedule_name={schedule_name}")
print(f"schedule_expression={schedule_expression}")
print(f"schedule_enabled={str(schedule_enabled).lower()}")
print(f"schedule_timezone={schedule_timezone}")

print(f"run_after_deploy={str(run_after_deploy).lower()}")