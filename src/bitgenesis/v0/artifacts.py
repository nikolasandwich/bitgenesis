"""Small durable-output helpers; no simulation rules or RNG use."""

import json
import os
from pathlib import Path
import tempfile


def write_json_atomic(path, value):
    """Replace a JSON checkpoint only after its complete contents reach disk.

    The temporary file shares the target directory, so replacement stays on the
    same filesystem. This preserves the preceding checkpoint if writing fails;
    it does not promise recovery from every filesystem or power-loss failure.
    """
    path = Path(path)
    payload = json.dumps(value, indent=2, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
