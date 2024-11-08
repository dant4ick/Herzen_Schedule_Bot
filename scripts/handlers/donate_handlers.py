import logging

from aiogram import F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from scripts.bot import dp, bot
from scripts.keyboards import inline_kb_donate
from scripts.utils import notify_admins

@dp.message(Command('donate'))
async def show_donate_methods(msg: Message):
    await msg.answer("Хочешь поддержать бота и его разработчика? Есть несколько способов:\n"
                     "💎 Однократный донат на любую сумму — ты сам выбираешь размер поддержки.\n"
                     "💸 Ежемесячная поддержка — вариант один, но он доступен каждому.\n"
                     "⭐ Или можешь поддержать звездочками!\n\n"
                     "Все проходит через безопасные сервисы, так что твои данные остаются в безопасности.",
                     reply_markup=inline_kb_donate)


@dp.callback_query(F.data == 'donate_stars')
async def donate_stars(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for i in [25, 50, 150, 300]:
        builder.add(InlineKeyboardButton(text=f'{i} ⭐', callback_data=f'stars_{i}'))
    
    await call.answer()
    await call.message.edit_text("Выбери количество звездочек, которое хочешь отправить.",
                                 reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith('stars_'))
async def donate_stars(call: CallbackQuery):    
    stars = int(call.data.split('_')[1])
    await call.message.answer_invoice(title="Поддержка бота",
                                      description="Поддержка бота и его разработчика",
                                      payload='donate_stars',
                                      currency='XTR', provider_token='',
                                      prices=[LabeledPrice(label='донат', amount=stars)])
    
    await call.answer()
    await call.message.delete()


@dp.pre_checkout_query(F.invoice_payload == 'donate_stars')
async def donate_stars_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def donate_stars_success(msg: Message):
    await notify_admins(f"🌟 Пользователь {msg.from_user.id} поддержал бота на {msg.successful_payment.total_amount} звездочек.")
    
    await msg.answer("Спасибо за поддержку! Твои звездочки помогут боту стать еще лучше 🌟")
    logging.info(f"User {msg.from_user.id} donated {msg.successful_payment.total_amount} stars.")
