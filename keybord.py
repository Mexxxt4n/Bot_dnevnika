from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню
main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 ДЗ на сегодня"), KeyboardButton(text="📚 ДЗ на завтра")],
        [KeyboardButton(text="📅 ДЗ на неделю"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="🔔 Уведомления")],
        [KeyboardButton(text="🕐 Следующий урок"), KeyboardButton(text="🆘 Помощь")]
    ],
    resize_keyboard=True
)

# Меню расписания
schedule_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 На сегодня"), KeyboardButton(text="📅 На завтра")],
        [KeyboardButton(text="📅 Понедельник"), KeyboardButton(text="📅 Вторник")],
        [KeyboardButton(text="📅 Среда"), KeyboardButton(text="📅 Четверг")],
        [KeyboardButton(text="📅 Пятница")],
        [KeyboardButton(text="🔙 Назад в меню")]
    ],
    resize_keyboard=True
)

# Меню уведомлений
notify_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Включить уведомления"), KeyboardButton(text="❌ Отключить уведомления")],
        [KeyboardButton(text="🔙 Назад в меню")]
    ],
    resize_keyboard=True
)
