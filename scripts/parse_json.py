import json
import re
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

required_fields = ("name", "repository", "version")
for field in required_fields:
    if field not in data or str(data[field]).strip() == "":
        sys.exit(f"Missing required field: {field}")

name = str(data["name"]).strip()
repository = str(data["repository"]).strip()
version = str(data["version"]).strip()


def slugify(value: str) -> str:
    """Convierte a un identificador seguro para nombres AWS (simple)."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9-_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


name_slug = slugify(name)

# Base names (Terraform añadirá -dev / -qa con var.environment)
# Si no vienen en JSON, usamos defaults simples.
lambda_name = str(data.get("lambda_name") or "scraper").strip()
state_machine_name = str(data.get("state_machine_name") or "scraper").strip()
schedule_name = str(data.get("schedule_name") or "scraper").strip()

# Schedule expression default (si no viene)
schedule_expression = str(data.get("schedule_expression") or "cron(0 10 * * ? *)").strip()

# Campos opcionales
description = str(data.get("description", "")).strip()

# Outputs para GitHub Actions (GITHUB_OUTPUT)
print(f"name={name}")
print(f"description={description}")
print(f"repository={repository}")
print(f"version={version}")

# Outputs para Terraform
print(f"lambda_name={lambda_name}")
print(f"state_machine_name={state_machine_name}")
print(f"schedule_name={schedule_name}")
print(f"schedule_expression={schedule_expression}")
