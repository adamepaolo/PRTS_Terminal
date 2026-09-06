import json
import os


def load_history(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception as e:
        print(f"[WARNING] Could not load history file ({e}); starting fresh.")
    return []


def save_history(path, history):
    try:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(history, f, indent=2)
        os.replace(tmp_path, path)
    except Exception as e:
        print(f"[WARNING] Could not save history: {e}")
