import json
import uuid
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def rollback(self, target_uuid: str = None):
    """Rollback to a previous snapshot or current if not provided"""
    assert self.connection, "Connection not initialized"
    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if not target_uuid:
                cur.execute("""
                    SELECT * FROM db_vsg
                    WHERE is_current = TRUE
                    ORDER BY created_at DESC LIMIT 1
                """)
            else:
                cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (target_uuid,))
            original = cur.fetchone()
            if not original:
                logger.warning(f"Rollback UUID {target_uuid or '[current]'} not found.")
                return None

            blob_data = json.loads(original["blob"])
            table = blob_data["table"]
            previous_state = blob_data.get("before") or []

            cur.execute(f"DELETE FROM {table}")
            for row in previous_state:
                keys = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                cur.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(row.values()))

            new_uuid = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            user = self.user_callback() if self.user_callback else "system"

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            new_state = [dict(r) for r in cur.fetchall()]

            cur.execute(load_sql("not_current.sql"), {"table": table})

            blob = json.dumps({
                "uuid": new_uuid,
                "operation": "ROLLBACK",
                "query": f"ROLLBACK para UUID {original['uuid']}",
                "table": table,
                "record_id": None,
                "user": user,
                "timestamp": now,
                "before": blob_data.get("state"),
                "after": new_state,
                "state": new_state,
                "meta": {
                    "rollbacked_from": original["uuid"],
                    "table": table,
                    "parent": original["uuid"]
                }
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob)
            rollback_sql = load_sql("rollback.sql")
            cur.execute(rollback_sql, {
                "uuid": new_uuid,
                "operation": "ROLLBACK",
                "query": f"ROLLBACK para UUID {original['uuid']}",
                "meta": json.dumps({
                    "rollbacked_from": original["uuid"],
                    "table": table,
                    "parent": original["uuid"]
                }),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob,
                "rollbacked_from": original["uuid"],
                "parent_uuid": original["uuid"]
            })

            self.connection.commit()
            logger.info(f"Rollback created as new UUID {new_uuid}")
            return new_uuid

    except Exception as e:
        logger.error(f"Rollback - (FAILED) - {str(e)}")
        raise
