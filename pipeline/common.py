from pathlib import Path
import json, os

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("NFL_CSV", "/Users/Aydan/Library/Mobile Documents/com~apple~CloudDocs/nfl2025events.csv"))
PROCESSED = ROOT / "data" / "processed"
PUBLIC = ROOT / "public" / "data"
BOOL_COLS = ["PLAY_CNTS", "EFF_CNTS", "FROM_SCRIMMAGE", "IS_TWOMIN", "IS_FIRST_DOWN", "IS_SCORING_PLAY", "POS_CHANGE", "CONTINUATION", "BLITZ", "PLAY_ACTION", "SCREEN_PASS", "IS_MOTION", "CATCHABLE_PASS", "WAS_RECEIVER_OPEN", "POORLY_THROWN"]

def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def publish_json(name, payload):
    write_json(PROCESSED / name, payload)
    write_json(PUBLIC / name, payload)
