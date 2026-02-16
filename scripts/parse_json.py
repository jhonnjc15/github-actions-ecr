import json
import re
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

# ------------------------------------------------------------
# REQUIRED FIELDS (multi-stack)
# ------------------------------------------------------------
required_fields = ("id", "repository", "version")
for field in required_fields:
    if field not in data or str(data[field]).strip() == "":
        sys.exit(f"Missing required field: {field}")

stack_id_raw = str(data["id"]).strip()
repository = str(data["repository"]).strip()
version = str(data["version"]).strip()

# name pasa a ser opcional (solo display)
name = str(data.get("name") or stack_id_raw).strip()


def slugify(value: str) -> str:
    """Convierte a un identificador seguro para nombres AWS (simple)."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9-_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


stack_id = slugify(stack_id_raw)

# Base names (Terraform añadirá -<env>-<stack_id>)
lambda_name = str(data.get("lambda_name") or data.get("id")).strip()
state_machine_name = str(data.get("state_machine_name") or data.get("id")).strip()
schedule_name = str(data.get("schedule_name") or data.get("id")).strip()

# Schedule expression default (si no viene)
schedule_expression = str(data.get("schedule_expression") or "cron(0 10 * * ? *)").strip()

# Campos opcionales
description = str(data.get("description", "")).strip()

# ------------------------------------------------------------
# Outputs para GitHub Actions (GITHUB_OUTPUT)
# ------------------------------------------------------------
print(f"id={stack_id}")                 # <- clave para backend y nombres
print(f"name={name}")                  # <- solo display
print(f"description={description}")
print(f"repository={repository}")
print(f"version={version}")

# Outputs para Terraform
print(f"stack_id={stack_id}")          # <- por claridad (igual que id)
print(f"lambda_name={lambda_name}")
print(f"state_machine_name={state_machine_name}")
print(f"schedule_name={schedule_name}")
print(f"schedule_expression={schedule_expression}")
