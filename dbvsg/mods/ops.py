import uuid
import json
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def ops(self, *, query: str, operation: str, table: str, parent_uuid: str = None):
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

            # Obtem o HEAD atual
            cur.execute("""
                SELECT uuid FROM db_vsg
                WHERE meta->>'table' = %s AND is_current = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """, (table,))
            current = cur.fetchone()
            current_uuid = current["uuid"] if current else None

            # Se parent_uuid foi informado, validar
            if parent_uuid and parent_uuid != current_uuid:
                raise Exception(
                    f"Conflict: you are not based on the latest version ({current_uuid}). Your base was {parent_uuid}"
                )

            # Se não foi informado, usar o HEAD atual como parent
            effective_parent = parent_uuid or current_uuid

            # Captura estado antes e depois
            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            before = cur.fetchall()

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            after = cur.fetchall()

            # Criar blob
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
                    "parent": effective_parent
                }
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob)

            # Atualiza flags de is_current
            cur.execute(load_sql("not_current.sql"), {"table": table})
            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": operation,
                "query": query,
                "meta": json.dumps({
                    "record_id": record_id,
                    "table": table,
                    "parent": effective_parent
                }),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob,
                "parent_uuid": effective_parent,
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
