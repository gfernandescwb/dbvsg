import psycopg2
from ..utils.logger import logger

def conn(self, db_url, user_context=None):
    try:
        self.connection = psycopg2.connect(dsn=db_url)
        logger.info("Connecting to database - (SUCCESS)")
        if user_context:
            self.user_callback = user_context
    except Exception as e:
        logger.error(f"Connecting to database - (FAILED) - {str(e)}")
        raise
