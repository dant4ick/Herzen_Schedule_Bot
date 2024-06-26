from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import scripts.database as database
from data.config import TELEGRAM_TOKEN, BASE_DIR, CRYPTO_PAY_API_TOKEN, CRYPTO_PAY_API_NET

from aiocryptopay import AioCryptoPay, Networks

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

db = database.Database(Path(BASE_DIR / 'data/user_data.db'))

crypto = AioCryptoPay(CRYPTO_PAY_API_TOKEN, network=Networks.MAIN_NET if CRYPTO_PAY_API_NET == 'mainnet' else Networks.TEST_NET)
