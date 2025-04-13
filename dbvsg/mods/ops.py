import uuid
import json
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def ops(self, *, query: str, operation: str, table: str):
    assert self.connection

    try:
        user = self.user_callback() if self.user_callback else "system"
        now = datetime.now(timezone.utc).isoformat()

        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            inserted = cur.fetchone()
            record_id = inserted.get("id")
            if record_id is None:
                raise Exception("No record ID returned")

            cur.execute("""
                SELECT * FROM db_vsg
                WHERE meta->>'table' = %s AND is_current = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """, (table,))
            current = cur.fetchone()
            current_uuid = current["uuid"] if current else None

            if current and current["uuid"]:
                expected_parent = current["uuid"]

                cur.execute("""
                    SELECT parent_uuid FROM db_vsg
                    WHERE meta->>'table' = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (table,))
                latest = cur.fetchone()
                last_used_parent = latest["parent_uuid"] if latest else None

                if last_used_parent != expected_parent:
                    raise Exception(
                        f"Conflict: you are not based on the latest version ({expected_parent}). Your base was {last_used_parent}"
                    )

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            before = cur.fetchall()

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            after = cur.fetchall()

            new_uuid = str(uuid.uuid4())

            blob = json.dumps({
                "uuid": new_uuid,
                "operation": operation,
                "query": query,
                "table": table,
                "record_id": record_id,
                "user": user,
                "timestamp": now,
                "before": before,
                "after": after,
                "state": after,
                "meta": {
                    "record_id": record_id,
                    "table": table,
                    "parent": current_uuid
                }
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob)

            cur.execute(load_sql("not_current.sql"), {"table": table})
            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": operation,
                "query": query,
                "meta": json.dumps({
                    "record_id": record_id,
                    "table": table,
                    "parent": current_uuid
                }),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob,
                "parent_uuid": current_uuid,
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

        self.connection.commit()
        logger.info(f"{operation} committed as UUID {new_uuid}")
        return record_id

    except Exception as e:
        logger.error(f"{operation} failed - {str(e)}")
        raise
