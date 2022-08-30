import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import database
from config import TELEGRAM_TOKEN

logging.basicConfig(filename=datetime.now().strftime('logs/%d-%m-%Y_%H-%M.log'), level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

db = database.Database('user_data.db')
