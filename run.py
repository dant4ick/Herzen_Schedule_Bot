import argparse

import asyncio

from aiogram import Bot
from aiohttp import web

from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from data.config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, PUBLIC_KEY_PATH

from scripts.bot import dp, bot
from scripts.log_manager import log_rotation_and_archiving

from scripts.message_handlers import mailing_schedule
from scripts.parse import update_groups

import scripts.handlers  # Although it looks like an unused import, it is necessary for the handlers to be registered


async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    
    loop = asyncio.get_event_loop()
    loop.create_task(update_groups('00:00'))
    loop.create_task(mailing_schedule('18:00', 'tomorrow'))
    loop.create_task(log_rotation_and_archiving(bool(debug_mode)))

    if debug_mode:
        return
    
    if PUBLIC_KEY_PATH:
        await bot.set_webhook(WEBHOOK_URL, certificate=open(PUBLIC_KEY_PATH, 'rb'))
        return
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

    await dp.storage.close()


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    if debug_mode:
        await dp.start_polling(bot)
    else:
        # Create aiohttp.web.Application instance
        app = web.Application()
        
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        
        # Mount dispatcher startup and shutdown hooks to aiohttp application
        setup_application(app, dp, bot=bot)
        
        # And finally start webserver
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Run the bot in debug mode')
    args = parser.parse_args()

    debug_mode = args.debug
    asyncio.run(main())
