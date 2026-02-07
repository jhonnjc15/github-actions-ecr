# scripts/parse_config.py
import json
import re
import sys
from pathlib import Path


def sanitize(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace(" ", "-")
    s = re.sub(r"[^a-z0-9._/-]", "", s)
    return s


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/parse_config.py <config.json>", file=sys.stderr)
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"ERROR: config file not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Campos “humanos”
    name = data.get("name") or data.get("scraper_id")  # acepta ambos
    env = data.get("env")
    description = data.get("description", "")

    if not name:
        print("ERROR: missing required field: name (or scraper_id)", file=sys.stderr)
        sys.exit(1)
    if not env:
        print("ERROR: missing required field: env", file=sys.stderr)
        sys.exit(1)

    safe_name = sanitize(name)
    safe_env = sanitize(env)

    # Convenciones por defecto (Opción 1)
    default_ecr_repo = f"scrapers/{safe_env}/{safe_name}"
    default_lambda_name = f"scraper-{safe_env}-{safe_name}"
    default_sm_name = f"scraper-{safe_env}-{safe_name}-sm"
    default_schedule_name = f"scraper-{safe_env}-{safe_name}-schedule"
    default_schedule_expression = "rate(15 minutes)"

    # Permitir override desde JSON
    ecr_repo = data.get("ecr_repo") or default_ecr_repo
    lambda_name = data.get("lambda_name") or default_lambda_name
    state_machine_name = data.get("state_machine_name") or default_sm_name
    schedule_name = data.get("schedule_name") or default_schedule_name
    schedule_expression = data.get("schedule_expression") or default_schedule_expression

    # Validaciones mínimas
    if not ecr_repo:
        print("ERROR: ecr_repo resolved empty", file=sys.stderr)
        sys.exit(1)

    # Outputs para GitHub Actions ($GITHUB_OUTPUT)
    print(f"raw_name={name}")
    print(f"safe_name={safe_name}")
    print(f"env={env}")
    print(f"safe_env={safe_env}")
    print(f"description={description}")

    print(f"ecr_repo={ecr_repo}")
    print(f"lambda_name={lambda_name}")
    print(f"state_machine_name={state_machine_name}")
    print(f"schedule_name={schedule_name}")
    print(f"schedule_expression={schedule_expression}")


if __name__ == "__main__":
    main()
