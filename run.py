from asyncio import get_event_loop

# from aiogram import executor  # uncomment if not using webhooks

from data.config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, PUBLIC_KEY_PATH
from aiogram.utils.executor import start_webhook

from scripts.bot import dp, bot

from scripts.utils import mailing_schedule
from scripts.parse import parse_groups

import scripts.handlers


async def on_startup(dp):
    loop = get_event_loop()
    loop.create_task(mailing_schedule('18:00', 'tomorrow'))

    if PUBLIC_KEY_PATH:
        await bot.set_webhook(WEBHOOK_URL, certificate=open(PUBLIC_KEY_PATH, 'rb'))  # comment if not using webhooks
        return
    await bot.set_webhook(WEBHOOK_URL)  # comment if not using webhooks



async def on_shutdown(dp):
    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == "__main__":
    parse_groups()

    # executor.start_polling(dp, on_startup=on_startup, skip_updates=True)  # uncomment if not using webhooks
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
