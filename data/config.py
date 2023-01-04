import os
from pathlib import Path


# Telegram data
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_TELEGRAM_ID = int(os.environ.get('ADMIN_TELEGRAM_ID'))


# Webhook data
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
WEBHOOK_PATH = '/Herzen_Schedule_Bot'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = int(os.environ.get('WEBAPP_PORT'))

# for self-signed certificates
PUBLIC_KEY_PATH = os.environ.get('PUBLIC_KEY_PATH')
if PUBLIC_KEY_PATH:
    PUBLIC_KEY_PATH = Path(PUBLIC_KEY_PATH)


# Donate urls
DONATE_URL = os.environ.get('DONATE_URL')
SUBSCRIBE_URL = os.environ.get('SUBSCRIBE_URL')


# Path to run.py dir
BASE_DIR = Path(__file__).parent.parent
