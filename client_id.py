import uuid
from pathlib import Path

CLIENT_ID_FILE = "client_id.txt"


def get_client_id() -> str:
    path = Path(CLIENT_ID_FILE)
    if path.exists():
        return path.read_text().strip()
    client_id = str(uuid.uuid4())
    path.write_text(client_id)
    return client_id
