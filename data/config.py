import os
import sys
from pathlib import Path

from loguru import logger


if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()
    
FILES_DIR = os.path.join(ROOT_DIR, 'files')

LOG_FILE = os.path.join(FILES_DIR, 'log.log')
ERRORS_FILE = os.path.join(FILES_DIR, 'errors.log')

IMPORT_FILE = os.path.join(FILES_DIR, 'import.csv')
SETTINGS_FILE = os.path.join(FILES_DIR, 'settings.json')
COMPLETED_ACTIONS = os.path.join(FILES_DIR, 'completed_actions.json')
WALLETS_DB = os.path.join(FILES_DIR, 'wallets.db')


logger.add(ERRORS_FILE, level='ERROR')
logger.add(LOG_FILE, level='INFO')
