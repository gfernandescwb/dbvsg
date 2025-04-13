import logging
from pathlib import Path

LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "db_vsg.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("db_vsg")
