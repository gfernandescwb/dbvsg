import json
import uuid
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def merge(self, incoming_uuid: str):
    assert self.connection

    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM db_vsg
                WHERE is_current = TRUE
                ORDER BY created_at DESC LIMIT 1
            """)
            current = cur.fetchone()

            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (incoming_uuid,))
            incoming = cur.fetchone()

            if not current or not incoming:
                raise Exception("Missing snapshots for merge")

            blob_current = json.loads(current["blob"])
            blob_incoming = json.loads(incoming["blob"])
            table = blob_current["table"]

            combined = {row["id"]: row for row in blob_current["state"]}
            for row in blob_incoming["state"]:
                combined[row["id"]] = row
            merged_state = list(combined.values())

            new_uuid = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            user = self.user_callback() if self.user_callback else "system"

            blob = json.dumps({
                "uuid": new_uuid,
                "operation": "MERGE",
                "query": f"MERGE with {incoming_uuid}",
                "table": table,
                "record_id": None,
                "user": user,
                "timestamp": now,
                "before": blob_current["state"],
                "after": merged_state,
                "state": merged_state,
                "meta": {
                    "merged_from": incoming_uuid,
                    "parent": current["uuid"],
                    "table": table
                }
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob)

            cur.execute(load_sql("not_current.sql"), {"table": table})
            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": "MERGE",
                "query": f"MERGE with {incoming_uuid}",
                "meta": json.dumps({
                    "merged_from": incoming_uuid,
                    "parent": current["uuid"],
                    "table": table
                }),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob,
                "parent_uuid": current["uuid"],
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

            self.connection.commit()
            logger.info(f"Merge created as UUID {new_uuid}")
            return new_uuid

    except Exception as e:
        logger.error(f"Merge failed - {str(e)}")
        raise
