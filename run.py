import logging

# from aiogram import executor  # uncomment if not using webhooks

from aiogram.utils.executor import start_webhook

from scripts.bot import dp, bot

from scripts.parse import parse_groups

from data.config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, PUBLIC_KEY_PATH

import scripts.handlers


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL, certificate=open(PUBLIC_KEY_PATH, 'rb'))


async def on_shutdown(dp):
    logging.warning('shutting down..')

    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('bye!')


if __name__ == "__main__":
    parse_groups()
    # executor.start_polling(dp, skip_updates=True)  # uncomment if not using webhooks
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
