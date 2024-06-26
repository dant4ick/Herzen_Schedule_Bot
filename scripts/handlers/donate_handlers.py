import logging
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiocryptopay.const import Fiat
from aiocryptopay.const import CurrencyType
from aiocryptopay.models.update import Update

from scripts.bot import dp, crypto
from scripts.keyboards import inline_kb_donate, inline_kb_donate_amount, inline_bt_cancel


@dp.message_handler(commands=['donate'])
async def show_donate_methods(msg: Message):
    await msg.answer("Хочешь поддержать бота и его разработчика?\n"
                     "Вариантов несколько:\n"
                     "💎 Прислать состояньице любого размера, решаешь ты.\n"
                     "💸 Раз в месяц жаловать мелочишку, размер, опять же, определяешь ты.\n\n"
                     "Оформляется все через специальный сервис, так что никаких данных себе не сохраняю, "
                     "махинаций не провожу.",
                     reply_markup=inline_kb_donate)
    

@dp.callback_query_handler(text='crypto')
async def show_crypto_methods(call: CallbackQuery):        
    await call.message.edit_text("Выбери сумму, которую хочешь перевести", reply_markup=inline_kb_donate_amount)


@dp.callback_query_handler(lambda c: c.data.startswith('crypto_'))
async def process_crypto_payment(call: CallbackQuery):
    amount = int(call.data.split('_')[1])
    invoice = await crypto.create_invoice(amount, fiat=Fiat.RUB, currency_type=CurrencyType.FIAT,
                                          allow_comments=True, allow_anonymous=True, description="Поддержка бота",
                                          hidden_message="Спасибо за поддержку!",
                                          payload=str(call.from_user.id))
    
    kb_crypto_pay = InlineKeyboardMarkup().add(InlineKeyboardButton(text=f"Задонатить {amount}RUB в криптовалюте", url=invoice.mini_app_invoice_url)).row(inline_bt_cancel)
    
    await call.message.edit_text(f"Счет для оплаты доступен по кнопке "
                                 f"или по <a href='{invoice.bot_invoice_url}'>ссылке</a>.",
                                 reply_markup=kb_crypto_pay)


@crypto.pay_handler()
async def on_payment(update: Update):
    logging.info(f"Payment received: {update}")
    dp.bot.send_message(int(update.payload), f"Спасибо за поддержку! Ваш платеж на сумму {update.amount}RUB успешно обработан.")
