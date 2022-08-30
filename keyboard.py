from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

inline_bt_cancel = InlineKeyboardButton('Отменить', callback_data='cancel')

bt_group_config = KeyboardButton('⚙ Настройка группы ⚙')
bt_schedule_today = KeyboardButton('📗 Сегодня 📗')
bt_schedule_tomorrow = KeyboardButton('📘 Завтра 📘')
bt_schedule_week = KeyboardButton('7️⃣ Неделя 7️⃣')

kb_main = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add(bt_schedule_today, bt_schedule_tomorrow)\
    .row(bt_schedule_week).row(bt_group_config)
