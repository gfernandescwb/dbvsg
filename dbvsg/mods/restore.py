import json
from ..utils.logger import logger
import psycopg2.extras

def restore(self, uuid: str):
    assert self.connection, "Conexão não iniciada"
    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (uuid,))
            version = cur.fetchone()
            if not version:
                logger.warning(f"UUID {uuid} não encontrado para restore.")
                return None

            blob = json.loads(version["blob"])
            table = blob.get("table")
            state = blob.get("state")

            if not table or not state:
                logger.warning(f"Versão {uuid} não contém estado restaurável.")
                return None

            cur.execute(f"DELETE FROM {table}")
            for row in state:
                columns = ", ".join(row.keys())
                values = [row[k] for k in row]
                placeholders = ", ".join(["%s"] * len(values))
                cur.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)

            self.connection.commit()
            logger.info(f"Restore concluído da versão {uuid} para tabela '{table}'")
            return True

    except Exception as e:
        logger.error(f"Restore - (FAILED) - {str(e)}")
        raise
