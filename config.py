import os
from pathlib import Path

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_TELEGRAM_ID = int(os.environ.get('ADMIN_TELEGRAM_ID'))

WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
WEBHOOK_PATH = '/Herzen_Schedule_Bot'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = int(os.environ.get('WEBAPP_PORT'))

PUBLIC_KEY_PATH = Path(os.environ.get('PUBLIC_KEY_PATH'))  # for self-signed certificates

BASE_DIR = Path(__file__).parent
