import psycopg2.extras
from ..utils.logger import logger

def logs(self, table: str, limit: int = 20):
    assert self.connection, "Conexão não iniciada"
    try:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT uuid, operation, user_id, created_at,
                       is_current, rollbacked, is_deleted
                FROM db_vsg
                WHERE meta->>'table' = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (table, limit))

            results = cur.fetchall()
            logger.info(f"{len(results)} commits listados para a tabela '{table}'")
            return results

    except Exception as e:
        logger.error(f"Logs - (FAILED) - {str(e)}")
        raise
