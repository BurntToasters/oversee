import json
from pathlib import Path

DEFAULT_PATH = Path(".notes.json")


def load_notes(path: Path = DEFAULT_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_notes(notes: list[dict], path: Path = DEFAULT_PATH) -> None:
    path.write_text(json.dumps(notes, indent=2), encoding="utf-8")


def add_note(title: str, body: str, path: Path = DEFAULT_PATH) -> dict:
    notes = load_notes(path)
    next_id = max((n["id"] for n in notes), default=0) + 1
    note = {"id": next_id, "title": title, "body": body}
    notes.append(note)
    save_notes(notes, path)
    return note


def get_note(note_id: int, path: Path = DEFAULT_PATH) -> dict | None:
    for note in load_notes(path):
        if note["id"] == note_id:
            return note
    return None
