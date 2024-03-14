import os
from pathlib import Path


# Telegram data
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_TELEGRAM_ID = int(os.environ.get('ADMIN_TELEGRAM_ID', '123456789'))


# Webhook data
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
WEBHOOK_PATH = '/Herzen_Schedule_Bot'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = int(os.environ.get('WEBAPP_PORT', '5000'))

# for self-signed certificates
PUBLIC_KEY_PATH = os.environ.get('PUBLIC_KEY_PATH')
if PUBLIC_KEY_PATH:
    PUBLIC_KEY_PATH = Path(PUBLIC_KEY_PATH)


# Donate urls
DONATE_URL = os.environ.get('DONATE_URL', r'https://pay.cloudtips.ru/p/0a19cb8e')
SUBSCRIBE_URL = os.environ.get('SUBSCRIBE_URL', r'https://boosty.to/dant4ick')


# Path to run.py dir
BASE_DIR = Path(__file__).parent.parent
