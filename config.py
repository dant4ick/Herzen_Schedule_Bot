import os
from pathlib import Path

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_TELEGRAM_ID = os.environ.get('ADMIN_TELEGRAM_ID')

BASE_DIR = Path(__file__).parent
