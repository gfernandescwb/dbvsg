import json
import uuid
from datetime import datetime, timezone
import psycopg2.extras
from ..utils.logger import logger
from ..utils.read_sql import load_sql

def checkout(self, uuid: str):
    assert self.connection, "Conexão não iniciada"

    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (uuid,))
            version = cur.fetchone()
            if not version:
                logger.warning(f"UUID {uuid} não encontrado para checkout.")
                return None

            blob = json.loads(version["blob"])
            table = blob.get("table")
            state = blob.get("state")

            if not table or not state:
                logger.warning("Versão não possui state ou table definida.")
                return None

            cur.execute(f"DELETE FROM {table}")
            for row in state:
                keys = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                cur.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(row.values()))

            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            current_state = [dict(r) for r in cur.fetchall()]

            now = datetime.now(timezone.utc).isoformat()
            new_uuid = str(uuid.uuid4())
            user = self.user_callback() if self.user_callback else "system"

            cur.execute(load_sql("not_current.sql"), {"table": table})

            blob_checkout = json.dumps({
                "uuid": new_uuid,
                "operation": "CHECKOUT",
                "query": f"CHECKOUT from {uuid}",
                "table": table,
                "record_id": None,
                "user": user,
                "timestamp": now,
                "before": blob.get("state"),
                "after": current_state,
                "state": current_state,
                "meta": {"checkout_from": uuid, "table": table}
            }, sort_keys=True)

            hash_blob = self._hash_blob(blob_checkout)

            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": "CHECKOUT",
                "query": f"CHECKOUT from {uuid}",
                "meta": json.dumps({"checkout_from": uuid, "table": table}),
                "hash": hash_blob,
                "user_id": user,
                "blob": blob_checkout,
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

            self.connection.commit()
            logger.info(f"Checkout concluído com nova versão {new_uuid}")
            return new_uuid

    except Exception as e:
        logger.error(f"Checkout - (FAILED) - {str(e)}")
        raise
