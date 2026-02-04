import json
from pathlib import Path
from loguru import logger


def save_raw_data(data, filename, base_path="data/raw"):
    Path(base_path).mkdir(parents=True, exist_ok=True)
    file_path = Path(base_path) / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.success(f"Saved raw data to {file_path}")


# def load_json_file(filename, base_path="data/raw"):
#     """Load a JSON file and return the parsed object.

#     Returns the parsed JSON (dict/list) on success. If the file is missing, returns None.
#     Raises json.JSONDecodeError if the file contains invalid JSON, or other exceptions for I/O errors.
#     """
#     file_path = Path(base_path) / filename

#     if not file_path.exists():
#         logger.warning(f"JSON file not found: {file_path}")
#         return None

#     try:
#         with open(file_path, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to decode JSON from {file_path}: {e}")
#         raise
#     except Exception as e:
#         logger.error(f"Error reading JSON file {file_path}: {e}")
#         raise



