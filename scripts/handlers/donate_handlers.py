from aiogram.types import Message

from scripts.bot import dp
from scripts.keyboards import inline_kb_donate


@dp.message_handler(commands=['donate'])
async def show_donate_methods(msg: Message):
    await msg.answer("Хочешь поддержать бота и его разработчика?\n"
                     "Вариантов несколько:\n"
                     "💎 Прислать состояньице любого размера, решаешь ты.\n"
                     "💸 Раз в месяц жаловать мелочишку, размер можешь, опять же, определить ты.\n\n"
                     "Оформляется все через специальный сервис, так что никаких данных себе не сохраняю, "
                     "махинаций не провожу.\n\n"
                     "Если что-то тебе подходит, нажимай на кнопки снизу.\n"
                     "Новых функций ты не получишь - бот будет бесплатным для всех, "
                     "зато порадуешь админа и поддержишь проект.",
                     reply_markup=inline_kb_donate)
