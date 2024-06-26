import argparse

from asyncio import get_event_loop

from aiogram import executor

from data.config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, PUBLIC_KEY_PATH
from aiogram.utils.executor import start_webhook

from scripts.bot import dp, bot, crypto
from scripts.log_manager import log_rotation_and_archiving

from scripts.message_handlers import mailing_schedule
from scripts.parse import clear_schedule_cache, update_groups

import scripts.handlers


async def on_startup(dp):
    loop = get_event_loop()
    loop.create_task(update_groups('00:00'))

    loop.create_task(mailing_schedule('18:00', 'tomorrow'))
    loop.create_task(clear_schedule_cache('20:00'))
    
    if debug_mode:
        return

    loop.create_task(log_rotation_and_archiving())
    
    if PUBLIC_KEY_PATH:
        await bot.set_webhook(WEBHOOK_URL, certificate=open(PUBLIC_KEY_PATH, 'rb'))
        return
    await bot.set_webhook(WEBHOOK_URL)



async def on_shutdown(dp):
    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()
    
    await crypto.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Run the bot in debug mode')
    args = parser.parse_args()

    debug_mode = args.debug
    if debug_mode:
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    else:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
