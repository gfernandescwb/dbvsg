import uuid
import json
from datetime import datetime, timezone
from ..utils.logger import logger
from ..utils.read_sql import load_sql

def delete(self, target_uuid: str, deleted_by: str = "system"):
    assert self.connection, "Connection not started"
    try:
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (target_uuid,))
            original = cur.fetchone()

            if not original:
                logger.warning(f"Delete UUID {target_uuid} not found.")
                return None

            user = self.user_callback() if self.user_callback else deleted_by
            new_uuid = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            meta = json.loads(original[3]) if original[3] else {}
            blob = json.dumps({
                "uuid": new_uuid,
                "operation": "DELETE",
                "query": original[2],
                "meta": meta,
                "user": user,
                "deleted_by": user,
                "deleted_at": now,
                "rollbacked_from": target_uuid
            }, sort_keys=True)
            hash_blob = self._hash_blob(blob)

            if "record_id" in meta:
                sql_clear = load_sql("not_current.sql")
                cur.execute(sql_clear, {"record_id": str(meta["record_id"])})
            else:
                logger.warning("No 'record_id' in meta, unable to clear current flag")

            sql_insert = load_sql("delete_version.sql")
            cur.execute(sql_insert, {
                "uuid": new_uuid,
                "operation": "DELETE",
                "query": original[2],
                "meta": original[3],
                "hash": hash_blob,
                "user_id": user,
                "blob": blob,
                "rollbacked_from": target_uuid,
                "deleted_by": user,
                "deleted_at": now
            })

            self.connection.commit()
            logger.info(f"Soft delete version created for UUID {target_uuid} as new UUID {new_uuid}")
            return new_uuid

    except Exception as e:
        logger.error(f"Soft delete on {target_uuid} - (FAILED) - {str(e)}")
        raise
