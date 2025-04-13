from ..utils.logger import logger
from ..utils.read_sql import load_sql

def ensure_table(self):
    assert self.connection, "Conexão não iniciada"
    try:
        with self.connection.cursor() as cur:
            sql = load_sql("create_table.sql")
            cur.execute(sql)
        self.connection.commit()
        logger.info("Table check/creation - (SUCCESS)")
    except Exception as e:
        logger.error(f"Table creation failed - (FAILED) - {str(e)}")
        raise
