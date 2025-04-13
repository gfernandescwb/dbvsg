import uuid
import json
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def ops(self, *, query: str, operation: str, table: str):
    assert self.connection, "Conexão não iniciada"
    try:
        user = self.user_callback() if self.user_callback else "system"
        uid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            result = cur.fetchone()
            record_id = result["id"]

            cur.execute(f"SELECT * FROM {table} WHERE id = %s", (record_id,))
            after = cur.fetchone()
            after_dict = dict(after) if after else None

            cur.execute("SELECT * FROM db_vsg WHERE is_current = TRUE AND meta->>'table' = %s", (table,))
            current = cur.fetchone()
            before_dict = json.loads(current["blob"])["state"] if current else []

            cur.execute(load_sql("not_current.sql"), {"table": table})

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            all_rows = cur.fetchall()
            state_snapshot = [dict(row) for row in all_rows]

            blob = json.dumps({
                "uuid": uid,
                "operation": operation,
                "table": table,
                "record_id": record_id,
                "user": user,
                "timestamp": now,
                "before": before_dict,
                "after": after_dict,
                "state": state_snapshot,
                "meta": {
                    "record_id": record_id,
                    "table": table
                }
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob)

            sql_insert = load_sql("insert_audit.sql")
            cur.execute(sql_insert, {
                "uuid": uid,
                "operation": operation,
                "query": query,
                "meta": json.dumps({"record_id": record_id, "table": table}),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob,
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

        self.connection.commit()
        logger.info(f"{operation} - Snapshot and Commit (GLOBAL) - ID {record_id}")
        return record_id

    except Exception as e:
        logger.error(f"{operation} - (FAILED) - {str(e)}")
        raise
