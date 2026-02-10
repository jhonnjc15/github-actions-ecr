import json
import re
import sys
from pathlib import Path


data = json.loads(Path(sys.argv[1]).read_text())

for field in ("name", "env"):
    if field not in data:
        sys.exit(f"Missing required field: {field}")


name = str(data["name"]).strip()
env = str(data["env"]).strip()


def slugify(value: str) -> str:
    """Convierte a un identificador seguro para nombres AWS (simple)."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9-_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


name_slug = slugify(name)
env_slug = slugify(env)

# Defaults derivados (pueden sobreescribirse en el JSON si quieres control fino)
lambda_name = data.get("lambda_name") or f"scraper-{env_slug}-{name_slug}"[:64]
state_machine_name = data.get("state_machine_name") or f"{lambda_name}-sm"[:80]
schedule_name = data.get("schedule_name") or f"{lambda_name}-schedule"[:64]

# OJO: si no lo defines, dejamos un default razonable (1 vez al día a las 10:00 UTC)
# Puedes cambiarlo en el JSON con "schedule_expression".
schedule_expression = data.get("schedule_expression") or "cron(0 10 * * ? *)"


print(f"name={name}")
print(f"env={env}")
print(f"description={data.get('description','')}")
print(f"repository={data.get('repository','')}")
print(f"version={data.get('version','')}")

# Outputs para Terraform
print(f"lambda_name={lambda_name}")
print(f"state_machine_name={state_machine_name}")
print(f"schedule_name={schedule_name}")
print(f"schedule_expression={schedule_expression}")