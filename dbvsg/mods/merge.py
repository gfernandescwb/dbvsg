import json
import uuid
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql
import psycopg2.extras

def merge(self, incoming_uuid: str):
    assert self.connection, "Conexão não iniciada"
    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (incoming_uuid,))
            incoming = cur.fetchone()
            if not incoming:
                logger.warning(f"Versão {incoming_uuid} não encontrada para merge.")
                return None

            incoming_blob = json.loads(incoming["blob"])
            table = incoming_blob["table"]
            incoming_state = incoming_blob["state"]

            cur.execute(f"DELETE FROM {table}")
            for row in incoming_state:
                keys = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                cur.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(row.values()))

            cur.execute(load_sql("not_current.sql"), {"table": table})

            new_uuid = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            user = self.user_callback() if self.user_callback else "system"

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            final_state = [dict(r) for r in cur.fetchall()]

            merged_blob = json.dumps({
                "uuid": new_uuid,
                "operation": "MERGE",
                "query": f"MERGE com {incoming_uuid}",
                "table": table,
                "record_id": None,
                "user": user,
                "timestamp": now,
                "before": incoming_blob.get("state"),
                "after": final_state,
                "state": final_state,
                "meta": {"merged_from": incoming_uuid, "table": table}
            }, sort_keys=True)

            hash_blob = self._hash_blob(merged_blob)
            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": "MERGE",
                "query": f"MERGE com {incoming_uuid}",
                "meta": json.dumps({"merged_from": incoming_uuid, "table": table}),
                "hash": hash_blob,
                "user_id": user,
                "blob": merged_blob,
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

            self.connection.commit()
            logger.info(f"Merge aplicado com nova versão {new_uuid}")
            return new_uuid

    except Exception as e:
        logger.error(f"Merge - (FAILED) - {str(e)}")
        raise
