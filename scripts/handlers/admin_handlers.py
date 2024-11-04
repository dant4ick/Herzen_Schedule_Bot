import asyncio
from datetime import timedelta

from aiogram import types
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery

from scripts.bot import dp, db

from data.config import ADMIN_TELEGRAM_ID
from scripts import keyboards
from scripts.states import Broadcast
from scripts.message_handlers import broadcast_message


@dp.message_handler(commands=['admin'])
async def show_admin_menu(msg: Message):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        await msg.answer("Привет, админ!", reply_markup=keyboards.kb_admin)


@dp.message_handler(filters.Text(contains='вернуть клавиатуру пользователя', ignore_case=True))
async def show_admin_menu(msg: Message):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        await msg.answer("Пока, админ!", reply_markup=keyboards.kb_main)


@dp.message_handler(filters.Text(contains='отправить сообщение всем', ignore_case=True))
async def get_broadcast_message(msg: types.Message):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        await msg.answer("Пришлите сообщение, которое нужно разослать всем пользователям...")
        await Broadcast.Message.set()


@dp.message_handler(state=Broadcast.Message, content_types=types.ContentType.ANY)
async def confirm_broadcast_message(msg: types.Message, state: FSMContext):
    if msg.from_user.id == ADMIN_TELEGRAM_ID:
        async with state.proxy() as data:
            data['message'] = msg

        await msg.forward(ADMIN_TELEGRAM_ID)
        await msg.answer("Вы хотите переслать сообщение или отправить копию от имени бота?",
                         reply_markup=InlineKeyboardMarkup().add(
                             keyboards.InlineKeyboardButton("Переслать", callback_data="forward"),
                             keyboards.InlineKeyboardButton("Отправить копию", callback_data="copy"),
                         ).row(keyboards.inline_bt_cancel))
        await Broadcast.next()


@dp.callback_query_handler(state=Broadcast.MessageType)
async def send_broadcast_message(call: CallbackQuery, state: FSMContext):
    if call.from_user.id == ADMIN_TELEGRAM_ID:
        await call.answer()
        async with state.proxy() as data:
            msg = data['message']
        msg_type = call.data
        await state.finish()

        all_id = db.get_all_id()
        all_id.remove((ADMIN_TELEGRAM_ID,))

        max_counter = len(all_id)
        update_interval = max(1, max_counter // 100)  # Update every 1% or at least every user if less than 100 users

        await call.bot.send_message(ADMIN_TELEGRAM_ID, f"Это займет примерно {timedelta(seconds=max_counter * 0.5)}.")
        await call.message.edit_text(f"Хорошо, отправляю {max_counter} сообщений...")

        for msg_counter, user_id in enumerate(all_id, start=1):
            await broadcast_message(user_id[0], msg, msg_type)
            
            if msg_counter % update_interval == 0 or msg_counter == max_counter:
                progress = (msg_counter / max_counter) * 100
                progress_bar = f"<code>[{'#' * (int(progress) // 5)}{'-' * (20 - (int(progress) // 5))}]</code>"
                await call.message.edit_text(f"Отправлено {msg_counter} из {max_counter} ({progress:.2f}%) {progress_bar}")
            
            await asyncio.sleep(.5)
