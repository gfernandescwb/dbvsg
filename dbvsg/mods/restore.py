import json
from ..utils.logger import logger
import psycopg2.extras

def restore(self, uuid: str):
    assert self.connection

    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (uuid,))
            snapshot = cur.fetchone()
            if not snapshot:
                return False

            blob = json.loads(snapshot["blob"])
            table = blob["table"]
            state = blob["state"]

            cur.execute(f"DELETE FROM {table}")
            for row in state:
                keys = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                cur.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(row.values()))

            self.connection.commit()
            logger.info(f"Restored table {table} to snapshot {uuid}")
            return True

    except Exception as e:
        logger.error(f"Restore failed - {str(e)}")
        raise
