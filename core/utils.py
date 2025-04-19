import json
import logging
import sqlite3
from datetime import datetime, date, time

# Register adapters and converters so sqlite3 can handle datetime objects directly
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda b: datetime.fromisoformat(b.decode()))
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_converter("DATE", lambda b: date.fromisoformat(b.decode()))
sqlite3.register_adapter(time, lambda t: t.isoformat())
sqlite3.register_converter("TIME", lambda b: time.fromisoformat(b.decode()))

def to_bool_int(value: bool) -> int:
    """Convert a boolean to an integer (1 or 0) for SQLite storage."""
    return 1 if value else 0

def from_bool_int(value: int) -> bool:
    """Convert an integer (1 or 0) from SQLite to a boolean."""
    return bool(value)

def safe_json_loads(json_string, default_value, field_name, context=""):
    if not json_string:
        return default_value
    try:
        return json.loads(json_string)  # ← use json.loads, not self.safe_json_loads
    except json.JSONDecodeError as e:
        logging.warning(
            f"Malformed JSON detected for field '{field_name}' {context}. "
            f"Error: {e}. Using default: {default_value!r}. "
            f"JSON string was: '{json_string[:100]}{'...' if len(json_string) > 100 else ''}'"
        )
        return default_value
    except Exception as e:
        logging.error(
            f"Unexpected error loading JSON for field '{field_name}' {context}. "
            f"Error: {e}. Using default: {default_value!r}. "
            f"JSON string was: '{json_string[:100]}{'...' if len(json_string) > 100 else ''}'"
        )
        return default_value


def safe_json_dumps(python_object, default_json_string, field_name, context=""):
    """Safely dump Python object to JSON string, returning default on error."""
    if python_object is None:
        # Decide if None should map to 'null' or be handled by the caller
        # For DB storage, often None itself is preferred over 'null' string.
        # Let's return None here, and let the DB insert handle it.
        return None
    try:
        # Ensure datetime objects are handled if they sneak in (though Task class aims to prevent this)
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

        return json.dumps(python_object, default=default_serializer)
    except TypeError as e:
        logging.warning(
            f"Could not serialize field '{field_name}' {context} to JSON. Error: {e}. Using default: {default_json_string!r}. Object was: {python_object!r}")
        return default_json_string
    except Exception as e:  # Catch other potential errors during dumping
        logging.error(
            f"Unexpected error dumping JSON for field '{field_name}' {context}. Error: {e}. Using default: {default_json_string!r}. Object was: {python_object!r}")
        return default_json_string
