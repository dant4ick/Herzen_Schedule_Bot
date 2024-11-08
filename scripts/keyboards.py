from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

from data.config import DONATE_URL, SUBSCRIBE_URL

inline_bt_cancel = InlineKeyboardButton(text='Отменить', callback_data='cancel')
inline_bt_confirm = InlineKeyboardButton(text='Подтвердить', callback_data='confirm')

inline_kb_confirm = InlineKeyboardMarkup(inline_keyboard=[[inline_bt_confirm, inline_bt_cancel]])


bt_back = KeyboardButton(text='◀ Назад')

bt_settings = KeyboardButton(text='⚙ Настройки')
bt_schedule_today = KeyboardButton(text='📗 Сегодня')
bt_schedule_tomorrow = KeyboardButton(text='📘 Завтра')
bt_schedule_curr_week = KeyboardButton(text='🔽 Эта неделя')
bt_schedule_next_week = KeyboardButton(text='▶ Следующая неделя')

kb_main = ReplyKeyboardMarkup(keyboard=[
    [bt_schedule_today, bt_schedule_tomorrow], 
    [bt_schedule_curr_week, bt_schedule_next_week], 
    [bt_settings]], resize_keyboard=True)

bt_mailing_config = KeyboardButton(text='✉ Настройка рассылки')
bt_group_config = KeyboardButton(text='🤓 Настройка группы')

inline_bt_unsub = InlineKeyboardButton(text='Отписаться от рассылки', callback_data='unsubscribe')

kb_settings = ReplyKeyboardMarkup(keyboard=[[bt_mailing_config], [bt_group_config], [bt_back]], resize_keyboard=True)

inline_bt_donate = InlineKeyboardButton(text='Разовый платеж', url=DONATE_URL)
inline_bt_subscribe = InlineKeyboardButton(text='Регулярный платеж', url=SUBSCRIBE_URL)
inline_bt_stars = InlineKeyboardButton(text='⭐ Звездочки ⭐', callback_data='donate_stars')

inline_kb_donate = InlineKeyboardMarkup(inline_keyboard=[[inline_bt_donate, inline_bt_subscribe], [inline_bt_stars], [inline_bt_cancel]])

bt_admin_broadcast = KeyboardButton(text='✉ Отправить сообщение всем')
bt_admin_refund = KeyboardButton(text='⭐ Возврат звездочек')
bt_admin_return = KeyboardButton(text='◀ Вернуть клавиатуру пользователя')

kb_admin = ReplyKeyboardMarkup(keyboard=[[bt_admin_broadcast, bt_admin_refund], [bt_admin_return]], resize_keyboard=True)
