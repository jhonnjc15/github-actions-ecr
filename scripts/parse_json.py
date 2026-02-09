import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())

for field in ("name", "env"):
    if field not in data:
        sys.exit(f"Missing required  field: {field}")

print(f"name={data['name']}")
print(f"env={data['env']}")
print(f"description={data.get('description','')}")
print(f"repository={data.get('repository','')}")
print(f"version={data.get('version','')}")