import json
from ..utils.logger import logger

def diff(self, uuid_a: str, uuid_b: str):
    assert self.connection

    try:
        with self.connection.cursor() as cur:
            cur.execute("SELECT blob FROM db_vsg WHERE uuid = %s", (uuid_a,))
            row_a = cur.fetchone()
            cur.execute("SELECT blob FROM db_vsg WHERE uuid = %s", (uuid_b,))
            row_b = cur.fetchone()

        if not row_a or not row_b:
            raise Exception("One or both UUIDs not found")

        blob_a = json.loads(row_a[0])
        blob_b = json.loads(row_b[0])

        state_a = {str(item["id"]): item for item in blob_a.get("state", [])}
        state_b = {str(item["id"]): item for item in blob_b.get("state", [])}

        added = []
        removed = []
        changed = []

        for key in state_b:
            if key not in state_a:
                added.append(state_b[key])
            elif state_a[key] != state_b[key]:
                changed.append({"id": key, "from": state_a[key], "to": state_b[key]})

        for key in state_a:
            if key not in state_b:
                removed.append(state_a[key])

        return {
            "added": added,
            "removed": removed,
            "changed": changed
        }

    except Exception as e:
        logger.error(f"Diff failed - {str(e)}")
        raise
