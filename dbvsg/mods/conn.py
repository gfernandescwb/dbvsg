import psycopg2
from .ensure_table import ensure_table

from ..utils.logger import logger

def conn(self, db_url: str, user_context=None):
    try:
        self.connection = psycopg2.connect(dsn=db_url)
        self.user_callback = user_context
        ensure_table(self)
        logger.info("Connecting to database - (SUCCESS)")
    except Exception as e:
        logger.error(f"Connecting to database - (FAILED) - {str(e)}")
        raise
