from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

inline_bt_cancel = InlineKeyboardButton('Отменить', callback_data='cancel')
inline_bt_confirm = InlineKeyboardButton('Подтвердить', callback_data='confirm')

bt_group_config = KeyboardButton('⚙ Настройка группы ⚙')
bt_schedule_today = KeyboardButton('📗 Сегодня 📗')
bt_schedule_tomorrow = KeyboardButton('📘 Завтра 📘')
bt_schedule_curr_week = KeyboardButton('🔽 Эта неделя 7️⃣')
bt_schedule_next_week = KeyboardButton('▶ Следующая неделя 7️⃣')

kb_main = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add(bt_schedule_today, bt_schedule_tomorrow) \
    .row(bt_schedule_curr_week, bt_schedule_next_week).row(bt_group_config)

bt_admin_broadcast = KeyboardButton('✉ Отправить сообщение всем ✉')
bt_admin_return = KeyboardButton('◀ Вернуть клавиатуру пользователя ◀')

kb_admin = ReplyKeyboardMarkup(resize_keyboard=True).add(
    bt_admin_broadcast,
    bt_admin_return
)
