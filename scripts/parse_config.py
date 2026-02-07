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

    name = data.get("name")
    env = data.get("env")
    description = data.get("description", "")

    if not name:
        print("ERROR: missing required field: name", file=sys.stderr)
        sys.exit(1)
    if not env:
        print("ERROR: missing required field: env", file=sys.stderr)
        sys.exit(1)

    safe_name = sanitize(name)
    safe_env = sanitize(env)

    # Repo derivado (puedes cambiar la convención aquí)
    ecr_repo = data.get("ecr_repo") or f"scrapers/{safe_env}/{safe_name}"

    # Outputs para GitHub Actions ($GITHUB_OUTPUT)
    print(f"raw_name={name}")
    print(f"safe_name={safe_name}")
    print(f"env={env}")
    print(f"description={description}")
    print(f"ecr_repo={ecr_repo}")


if __name__ == "__main__":
    main()