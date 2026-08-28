"""Durable SQLite storage for Ailyn House Project."""
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "ailyn_house.db")
LEGACY_STATE_FILE = os.path.join(APP_DIR, "app_state.json")
BACKUP_DIR = os.path.join(APP_DIR, "backups")
SCANNER_PHOTO_DIR = os.path.join(APP_DIR, "archive", "scanner_photos")
PERSISTENT_KEYS = (
    "records", "labor_records", "payroll_expenses", "planner_tasks", "budget",
    "budget_history", "remaining_money", "view", "receipt_archive", "project", "scanner_photos", "dark_mode", "client_notes", "app_settings",
)


def _connect():
    connection = sqlite3.connect(DB_FILE)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _empty_state():
    return {
        "records": [], "labor_records": [], "payroll_expenses": [], "planner_tasks": [],
        "budget": 0.0, "budget_history": [], "remaining_money": 0.0,
        "view": "home", "receipt_archive": [], "scanner_photos": [], "dark_mode": False, "client_notes": [],
        "app_settings": {"display_name": "", "email": "", "client_mode": False, "email_notifications": True, "budget_alerts": True, "date_format": "%Y-%m-%d"},
        "project": {"name": "Ailyn House Project", "client": "", "address": "", "manager": "", "status": "Active", "target_date": ""},
    }


def initialize():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with _connect() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS state_history (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, changed_at TEXT NOT NULL)")
        row = connection.execute("SELECT payload FROM app_state WHERE id = 1").fetchone()
        if row is None:
            state = _load_legacy()
            payload = json.dumps(state, default=str)
            connection.execute("INSERT INTO app_state VALUES (1, ?, ?)", (payload, _now()))
            connection.execute("INSERT INTO state_history (payload, changed_at) VALUES (?, ?)", (payload, _now()))


def _load_legacy():
    if os.path.exists(LEGACY_STATE_FILE):
        try:
            with open(LEGACY_STATE_FILE, encoding="utf-8") as handle:
                raw = json.load(handle)
            return {key: raw[key] for key in PERSISTENT_KEYS if key in raw}
        except (OSError, json.JSONDecodeError):
            pass
    return _empty_state()


def _now():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    initialize()
    with _connect() as connection:
        row = connection.execute("SELECT payload FROM app_state WHERE id = 1").fetchone()
    if not row:
        return _empty_state()
    try:
        state = json.loads(row[0])
    except json.JSONDecodeError:
        return _empty_state()
    result = _empty_state()
    result.update({key: state[key] for key in PERSISTENT_KEYS if key in state})
    return result


def save_state(state):
    initialize()
    clean_state = {key: state.get(key, _empty_state()[key]) for key in PERSISTENT_KEYS}
    payload = json.dumps(clean_state, default=str)
    with _connect() as connection:
        connection.execute("UPDATE app_state SET payload = ?, updated_at = ? WHERE id = 1", (payload, _now()))
        connection.execute("INSERT INTO state_history (payload, changed_at) VALUES (?, ?)", (payload, _now()))
    return clean_state


def create_backup():
    initialize()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = os.path.join(BACKUP_DIR, f"ailyn_house_{timestamp}.db")
    with _connect() as source, sqlite3.connect(backup_path) as target:
        source.backup(target)
    return backup_path


def restore_backup(backup_path):
    if not os.path.isfile(backup_path):
        raise ValueError("Backup file was not found.")
    if os.path.abspath(backup_path) == os.path.abspath(DB_FILE):
        raise ValueError("Choose a backup file, not the active database.")
    create_backup()
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=APP_DIR, prefix=".restore-") as temporary:
            temporary_path = temporary.name
        with sqlite3.connect(backup_path) as source, sqlite3.connect(temporary_path) as target:
            source.backup(target)
        os.replace(temporary_path, DB_FILE)
    except (OSError, sqlite3.Error) as error:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise ValueError(f"Restore failed: {error}") from None
    return load_state()


def history_count():
    initialize()
    with _connect() as connection:
        return connection.execute("SELECT COUNT(*) FROM state_history").fetchone()[0]


def save_scanner_photo(photo_bytes, mime_type="image/jpeg", photo_id=None):
    """Save a captured scanner image under the application directory."""
    if not photo_bytes:
        raise ValueError("The captured photo is empty.")
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(mime_type)
    if extension is None:
        raise ValueError("Unsupported scanner photo format.")
    os.makedirs(SCANNER_PHOTO_DIR, exist_ok=True)
    filename = f"{photo_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}{extension}"
    target = os.path.join(SCANNER_PHOTO_DIR, filename)
    with tempfile.NamedTemporaryFile(delete=False, dir=SCANNER_PHOTO_DIR, prefix=".photo-") as temporary:
        temporary.write(photo_bytes)
        temporary_path = temporary.name
    os.replace(temporary_path, target)
    return os.path.relpath(target, APP_DIR)


def delete_scanner_photo(relative_path):
    """Delete a scanner image only when it belongs to the scanner photo directory."""
    if not relative_path:
        return False
    target = os.path.abspath(os.path.join(APP_DIR, relative_path))
    photo_root = os.path.abspath(SCANNER_PHOTO_DIR)
    if os.path.commonpath((target, photo_root)) != photo_root:
        raise ValueError("Invalid scanner photo path.")
    if os.path.isfile(target):
        os.remove(target)
        return True
    return False
