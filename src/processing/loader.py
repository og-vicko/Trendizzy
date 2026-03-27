import json
from pathlib import Path

def load_trends_from_json(filename, base_path="data/raw"):
    # Path(base_path).mkdir(parents=True, exist_ok=True)
    file_path = Path(base_path) / filename
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)