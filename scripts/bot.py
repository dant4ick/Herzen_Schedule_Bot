from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import scripts.database as database
from data.config import TELEGRAM_TOKEN, BASE_DIR

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

db = database.Database(Path(BASE_DIR / 'data/user_data.db'))
