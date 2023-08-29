from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import scripts.database as database
from data.config import TELEGRAM_TOKEN, BASE_DIR

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

db = database.Database(Path(BASE_DIR / 'data/user_data.db'))
