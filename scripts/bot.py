import logging
from pathlib import Path
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import scripts.database as database
from config import TELEGRAM_TOKEN, BASE_DIR

logging.basicConfig(#stream=open(Path(BASE_DIR / datetime.now().strftime('logs/%d-%m-%Y_%H-%M.log')),
                    #            'w', encoding='UTF-8'),
                    format='%(asctime)s - [%(levelname)s] - %(funcName)s - %(message)s',
                    level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

db = database.Database(Path(BASE_DIR / 'user_data.db'))
