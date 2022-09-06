import os.path

from aiogram import executor

from scripts.bot import dp

import scripts.handlers

from scripts.parse import parse_groups


if __name__ == "__main__":
    parse_groups()
    executor.start_polling(dp, skip_updates=True)
