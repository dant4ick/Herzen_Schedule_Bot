from aiogram import executor

from bot import dp

import handlers
import configuration_handlers

from parse import parse_groups

if __name__ == "__main__":
    parse_groups()
    executor.start_polling(dp, skip_updates=True)