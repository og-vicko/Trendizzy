import json
from pathlib import Path
from loguru import logger


def save_raw_data(data, filename, base_path="data/raw"):
    Path(base_path).mkdir(parents=True, exist_ok=True)
    file_path = Path(base_path) / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.success(f"Saved raw data to {file_path}")