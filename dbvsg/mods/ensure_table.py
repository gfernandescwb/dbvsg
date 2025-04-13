from ..utils.logger import logger
from ..utils.read_sql import load_sql

def ensure_table(self):
    assert self.connection, "Database connection not initialized"
    try:
        with self.connection.cursor() as cur:
            cur.execute(load_sql("create_table.sql"))
        self.connection.commit()
        logger.info("Table check/creation - (SUCCESS)")
    except Exception as e:
        logger.error(f"Table creation failed - (FAILED) - {str(e)}")
        raise
