import json
import uuid
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def checkout(self, target_uuid: str):
    assert self.connection

    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (target_uuid,))
            version = cur.fetchone()
            if not version:
                return None

            blob = json.loads(version["blob"])
            table = blob["table"]
            previous_state = blob["state"]

            cur.execute(f"DELETE FROM {table}")
            for row in previous_state:
                keys = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                cur.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(row.values()))

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            new_state = cur.fetchall()

            new_uuid = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            user = self.user_callback() if self.user_callback else "system"

            blob_new = json.dumps({
                "uuid": new_uuid,
                "operation": "CHECKOUT",
                "query": f"CHECKOUT from {target_uuid}",
                "table": table,
                "record_id": None,
                "user": user,
                "timestamp": now,
                "before": blob["state"],
                "after": new_state,
                "state": new_state,
                "meta": {
                    "checkout_from": target_uuid,
                    "parent": target_uuid,
                    "table": table
                }
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob_new)

            cur.execute(load_sql("not_current.sql"), {"table": table})
            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": "CHECKOUT",
                "query": f"CHECKOUT from {target_uuid}",
                "meta": json.dumps({
                    "checkout_from": target_uuid,
                    "parent": target_uuid,
                    "table": table
                }),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob_new,
                "parent_uuid": target_uuid,
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

            self.connection.commit()
            logger.info(f"Checkout created as new UUID {new_uuid}")
            return new_uuid

    except Exception as e:
        logger.error(f"Checkout failed - {str(e)}")
        raise
