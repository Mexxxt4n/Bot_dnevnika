from aiogram import F, Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram import Bot
from config import TOKEN
import app.keybord as kb
from correct_diary_parser import diary_parser
from notifications import subscribe_user, unsubscribe_user, is_subscribed
import os
import time

bot = Bot(token=TOKEN)
router = Router()

# --- Пример: команда для изменения куки ---
@router.message(Command("setcookie"))
async def set_cookie(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Использование: /setcookie <имя> <значение>")
        return
    name, value = parts[1], parts[2]
    diary_parser.update_cookie(name, value)
    diary_parser.save_cookies()  # 🔧 сохраняем сразу
    await message.answer(f"✅ Кука {name} обновлена и сохранена.")

# Словари для анти-флуда
user_last_message = {}
bot_start_time = None



@router.message(Command("setcookie"))
async def set_cookie(message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("⚠️ Использование: /setcookie <имя> <значение>")
            return
        name, value = parts[1], parts[2]
        diary_parser.update_cookie(name, value)
        await message.answer(f"✅ Кука {name} обновлена.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def dz_today(message: Message):
    await message.answer("🔄 Получаю домашние задания на сегодня...")
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_today()
    
    if not lessons:
        await message.answer("🎉 На сегодня домашних заданий нет!")
        return
    
    response = f"📚 Домашние задания на сегодня:\n\n"
    subjects_with_hw = []  # Предметы с домашкой
    
    for i, lesson in enumerate(lessons, 1):
        response += f"🕒 {lesson['time']}\n" if lesson.get('time') else ""
        response += f"📖 {lesson['subject']}\n"
        
        if lesson.get('topic'):
            response += f"📝 Тема: {lesson['topic']}\n"
        
        if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
            response += f"📋 ДЗ: Не задано\n"
        else:
            response += f"📋 Домашние задания:\n"
            for hw_item in lesson['homework_items']:
                if hw_item['text'] != 'Не задано':
                    response += f"   • {hw_item['text']}\n"
                    subjects_with_hw.append(lesson['subject'])
        
        if lesson['files']:
            response += f"📎 Файлов: {len(lesson['files'])}\n"
        
        response += "\n"
    
    await message.answer(response)
    

    
    await send_all_files(message, lessons)

async def dz_tomorrow(message: Message):
    await message.answer("🔄 Получаю домашние задания на завтра...")
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_tomorrow()
    
    if not lessons:
        await message.answer("🎉 На завтра домашних заданий нет!")
        return
    
    response = f"📚 Домашние задания на завтра:\n\n"
    subjects_with_hw = []
    
    for i, lesson in enumerate(lessons, 1):
        response += f"🕒 {lesson['time']}\n" if lesson.get('time') else ""
        response += f"📖 {lesson['subject']}\n"
        
        if lesson.get('topic'):
            response += f"📝 Тема: {lesson['topic']}\n"
        
        if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
            response += f"📋 ДЗ: Не задано\n"
        else:
            response += f"📋 Домашние задания:\n"
            for hw_item in lesson['homework_items']:
                if hw_item['text'] != 'Не задано':
                    response += f"   • {hw_item['text']}\n"
                    subjects_with_hw.append(lesson['subject'])
        
        if lesson['files']:
            response += f"📎 Файлов: {len(lesson['files'])}\n"
        
        response += "\n"
    
    await message.answer(response)



async def dz_tomorrow(message: Message):
    await message.answer("🔄 Получаю домашние задания на завтра...")
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_tomorrow()
    
    if not lessons:
        await message.answer("🎉 На завтра домашних заданий нет!")
        return
    
    response = f"📚 Домашние задания на завтра:\n\n"
    subjects_with_hw = []
    
    for i, lesson in enumerate(lessons, 1):
        response += f"🕒 {lesson['time']}\n" if lesson.get('time') else ""
        response += f"📖 {lesson['subject']}\n"
        
        if lesson.get('topic'):
            response += f"📝 Тема: {lesson['topic']}\n"
        
        if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
            response += f"📋 ДЗ: Не задано\n"
        else:
            response += f"📋 Домашние задания:\n"
            for hw_item in lesson['homework_items']:
                if hw_item['text'] != 'Не задано':
                    response += f"   • {hw_item['text']}\n"
                    subjects_with_hw.append(lesson['subject'])
        
        if lesson['files']:
            response += f"📎 Файлов: {len(lesson['files'])}\n"
        
        response += "\n"
    
    await message.answer(response)
    

# Функции анти-флуда
def set_bot_start_time():
    global bot_start_time
    bot_start_time = time.time()

def is_fresh_message(message: Message) -> bool:
    if bot_start_time is None:
        return True
    message_time = message.date.timestamp()
    return message_time >= bot_start_time

def check_flood(user_id: int, limit: int = 3) -> bool:
    current_time = time.time()
    if user_id in user_last_message:
        time_diff = current_time - user_last_message[user_id]
        if time_diff < limit:
            return True
    user_last_message[user_id] = current_time
    return False

def anti_flood(limit: int = 3):
    def decorator(func):
        async def wrapper(message: Message, *args, **kwargs):
            if not is_fresh_message(message):
                return
            if check_flood(message.from_user.id, limit):
                await message.answer(f"⏳ Слишком часто! Подождите {limit} секунды.")
                return
            return await func(message)
        return wrapper
    return decorator

# Функции для ДЗ
async def send_all_files(message: Message, lessons):
    all_files = []
    for lesson in lessons:
        all_files.extend(lesson['files'])
    
    if all_files:
        await message.answer(f"📦 Загружаю {len(all_files)} файлов...")
        downloaded_files = diary_parser.download_all_files(all_files)
        
        for file_info in downloaded_files:
            try:
                await message.reply_document(
                    FSInputFile(file_info['path']),
                    caption=f"📎 {file_info['name']}"
                )
            except Exception as e:
                await message.answer(f"❌ Ошибка при отправке файла {file_info['name']}: {e}")
        
        await message.answer("✅ Все файлы загружены!")

async def dz_today(message: Message):
    await message.answer("🔄 Получаю домашние задания на сегодня...")
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_today()
    
    if not lessons:
        await message.answer("🎉 На сегодня домашних заданий нет!")
        return
    
    response = f"📚 Домашние задания на сегодня:\n\n"
    for i, lesson in enumerate(lessons, 1):
        response += f"🕒 {lesson['time']}\n" if lesson.get('time') else ""
        response += f"📖 {lesson['subject']}\n"
        
        if lesson.get('topic'):
            response += f"📝 Тема: {lesson['topic']}\n"
        
        if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
            response += f"📋 ДЗ: Не задано\n"
        else:
            response += f"📋 Домашние задания:\n"
            for hw_item in lesson['homework_items']:
                if hw_item['text'] != 'Не задано':
                    response += f"   • {hw_item['text']}\n"
        
        if lesson['files']:
            response += f"📎 Файлов: {len(lesson['files'])}\n"
        response += "\n"
    
    await message.answer(response)
    await send_all_files(message, lessons)

async def dz_tomorrow(message: Message):
    await message.answer("🔄 Получаю домашние задания на завтра...")
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_tomorrow()
    
    if not lessons:
        await message.answer("🎉 На завтра домашних заданий нет!")
        return
    
    response = f"📚 Домашние задания на завтра:\n\n"
    for i, lesson in enumerate(lessons, 1):
        response += f"🕒 {lesson['time']}\n" if lesson.get('time') else ""
        response += f"📖 {lesson['subject']}\n"
        
        if lesson.get('topic'):
            response += f"📝 Тема: {lesson['topic']}\n"
        
        if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
            response += f"📋 ДЗ: Не задано\n"
        else:
            response += f"📋 Домашние задания:\n"
            for hw_item in lesson['homework_items']:
                if hw_item['text'] != 'Не задано':
                    response += f"   • {hw_item['text']}\n"
        
        if lesson['files']:
            response += f"📎 Файлов: {len(lesson['files'])}\n"
        response += "\n"
    
    await message.answer(response)
    await send_all_files(message, lessons)

async def dz_week(message: Message):
    await message.answer("🔄 Получаю домашние задания на неделю...")
    diary_parser.cleanup_downloaded_files()
    homework_data = diary_parser.parse_diary(0)
    
    if not homework_data:
        await message.answer("❌ Не удалось получить данные дневника")
        return
    
    all_lessons_files = []
    for day_name, lessons in homework_data.items():
        response = f"📅 {day_name}:\n\n"
        if not lessons:
            response += "Домашних заданий нет 🎉\n"
        else:
            for i, lesson in enumerate(lessons, 1):
                response += f"{i}. 🕒 {lesson['time']}\n" if lesson.get('time') else f"{i}. "
                response += f"   📖 {lesson['subject']}\n"
                
                if lesson.get('topic'):
                    response += f"   📝 Тема: {lesson['topic']}\n"
                
                if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
                    response += f"   📋 ДЗ: Не задано\n"
                else:
                    response += f"   📋 Домашние задания:\n"
                    for hw_item in lesson['homework_items']:
                        if hw_item['text'] != 'Не задано':
                            response += f"      • {hw_item['text']}\n"
                
                if lesson['files']:
                    response += f"   📎 Файлов: {len(lesson['files'])}\n"
                    all_lessons_files.extend(lesson['files'])
                response += "\n"
        
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(response)
    
    if all_lessons_files:
        await message.answer("📦 Загружаю все файлы за неделю...")
        downloaded_files = diary_parser.download_all_files(all_lessons_files)
        for file_info in downloaded_files:
            try:
                await message.reply_document(
                    FSInputFile(file_info['path']),
                    caption=f"📎 {file_info['name']}"
                )
            except Exception as e:
                await message.answer(f"❌ Ошибка при отправке файла {file_info['name']}: {e}")

# Функции расписания
async def send_schedule(message: Message, day: str, lessons: list):
    if not lessons:
        await message.answer(f"📅 В {day} уроков нет! 🎉")
        return
    
    response = f"📅 Расписание на {day}:\n\n"
    for i, lesson in enumerate(lessons, 1):
        response += f"{i}. 🕒 {lesson['time']}\n"
        response += f"   📖 {lesson['subject']}\n"
        response += f"   🚪 Каб. {lesson['room']}\n\n"
    await message.answer(response)


# Обработчики команд
@router.message(CommandStart())
@anti_flood(limit=5)
async def cmd_start(message: Message):
    await message.reply(
        "Здравствуйте, меня зовут Футабочка, я личный бот этой группы. "
        "Данный бот был создан человеком по имени Данил, его профиль @Mexxxt4n. "
        "По ошибке, по багу, обращайтесь к нему.\n\n"
        "Доступные команды:\n"
        "• Домашние задания (/dz_today, /dz_tomorrow, /dz_week)\n"
        "• Расписание уроков\n"
        "• Авто-напоминания в 17:00\n\n"
        "Используйте кнопки меню для навигации!",
        reply_markup=kb.main
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        'Помощь по боту:\n\n'
        'Основные команды:\n'
        '/start - Начало работы\n'
        '/help - Помощь\n\n'
        'Команды для ДЗ:\n'
        '/dz_today - Домашние задания на сегодня\n'
        '/dz_tomorrow - Домашние задания на завтра\n'
        '/dz_week - Все домашние задания на неделю\n\n'
        'По вопросам и багам обращайтесь к @Mexxxt4n'
    )

@router.message(Command("photo"))
@anti_flood(limit=5)
async def send_user_photos(message: Message):
    try:
        user_id = message.from_user.id
        profile_photos = await bot.get_user_profile_photos(user_id)
        if profile_photos.total_count > 0:
            photo_set = profile_photos.photos[0]
            largest_photo = max(photo_set, key=lambda x: x.file_size)
            await message.reply_photo(
                photo=largest_photo.file_id,
                caption="Ваша фотография профиля"
            )
        else:
            await message.reply("У вас нет фотографий профиля!")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")


# Обработчики кнопок ДЗ
@router.message(F.text == "🔙 Назад в меню")
@anti_flood(limit=2)
async def back_to_main(message: Message):
    await message.answer("Главное меню:", reply_markup=kb.main)

@router.message(F.text == "📚 ДЗ на сегодня")
@anti_flood(limit=5)
async def dz_today_button(message: Message):
    await dz_today(message)

@router.message(F.text == "📚 ДЗ на завтра")
@anti_flood(limit=5)
async def dz_tomorrow_button(message: Message):
    await dz_tomorrow(message)

@router.message(F.text == "📅 ДЗ на неделю")
@anti_flood(limit=10)
async def dz_week_button(message: Message):
    await dz_week(message)

@router.message(F.text == "🆘 Помощь")
async def help_button(message: Message):
    await cmd_help(message)

@router.message(Command("dz_today"))
@anti_flood(limit=5)
async def dz_today_command(message: Message):
    await dz_today(message)

@router.message(Command("dz_tomorrow"))
@anti_flood(limit=5)
async def dz_tomorrow_command(message: Message):
    await dz_tomorrow(message)

@router.message(Command("dz_week"))
@anti_flood(limit=10)
async def dz_week_command(message: Message):
    await dz_week(message)

# Обработчики расписания
@router.message(F.text == "📅 Расписание")
@router.message(Command("schedule"))
@anti_flood(limit=3)
async def schedule_menu(message: Message):
    await message.answer("📅 Выберите день недели:", reply_markup=kb.schedule_kb)

@router.message(F.text == "📅 На сегодня")
@anti_flood(limit=2)
async def schedule_today(message: Message):
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    today = days[time.localtime().tm_wday]
    if today == "воскресенье":
        await message.answer("🎉 Сегодня воскресенье - выходной!")
        return
    lessons = SCHEDULE.get(today, [])
    await send_schedule(message, today, lessons)

@router.message(F.text == "📅 На завтра")
@anti_flood(limit=2)
async def schedule_tomorrow(message: Message):
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    tomorrow_idx = (time.localtime().tm_wday + 1) % 7
    tomorrow = days[tomorrow_idx]
    if tomorrow == "воскресенье":
        await message.answer("🎉 Завтра воскресенье - выходной!")
        return
    lessons = SCHEDULE.get(tomorrow, [])
    await send_schedule(message, f"завтра ({tomorrow})", lessons)

@router.message(F.text.startswith("📅 "))
@anti_flood(limit=2)
async def schedule_by_day(message: Message):
    day_text = message.text.replace("📅 ", "").lower()
    day_mapping = {
        "пн": "понедельник", "вт": "вторник", "ср": "среда",
        "чт": "четверг", "пт": "пятница", "сб": "суббота", "вс": "воскресенье"
    }
    day = day_mapping.get(day_text, day_text)
    if day not in SCHEDULE:
        await message.answer("❌ Неверный день недели. Используйте кнопки меню.")
        return
    lessons = SCHEDULE[day]
    await send_schedule(message, day, lessons)

@router.message(F.text == "🕐 Следующий урок")
@anti_flood(limit=2)
async def next_lesson(message: Message):
    current_time = time.localtime()
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    today = days[current_time.tm_wday]
    if today == "воскресенье":
        await message.answer("🎉 Сегодня воскресенье! Следующий урок завтра.")
        return
    lessons = SCHEDULE.get(today, [])
    for lesson in lessons:
        start_time = lesson['time'].split('-')[0]
        lesson_hour = int(start_time.split(':')[0])
        lesson_minute = int(start_time.split(':')[1])
        if (lesson_hour > current_hour) or (lesson_hour == current_hour and lesson_minute > current_minute):
            time_left = f"через {lesson_hour - current_hour}ч {lesson_minute - current_minute}м"
            await message.answer(
                f"🕐 Следующий урок:\n"
                f"📖 {lesson['subject']}\n"
                f"🕒 {lesson['time']}\n"
                f"🚪 Каб. {lesson['room']}\n"
                f"⏰ {time_left}"
            )
            return
    await message.answer("🎉 Уроки на сегодня окончены!")

# Обработчики уведомлений
@router.message(F.text == "🔔 Уведомления")
@router.message(Command("notify"))
@anti_flood(limit=3)
async def notifications_menu(message: Message):
    user_id = message.from_user.id
    status = "✅ ВКЛ" if is_subscribed(user_id) else "❌ ВЫКЛ"
    await message.answer(
        f"🔔 Автоматические уведомления: {status}\n\n"
        f"Бот будет присылать ДЗ на завтра каждый день в 17:00",
        reply_markup=kb.notify_kb
    )

@router.message(F.text == "✅ Включить уведомления")
@anti_flood(limit=2)
async def enable_notifications(message: Message):
    user_id = message.from_user.id
    subscribe_user(user_id)
    await message.answer(
        "✅ Уведомления включены!\n\n"
        "📚 Теперь вы будете получать ДЗ на завтра каждый день в 17:00\n"
        "⏰ Чтобы отключить - используйте кнопку ниже",
        reply_markup=kb.notify_kb
    )
# Добавь эти команды в router.message обработчики

@router.message(Command("clear_cache"))
@anti_flood(limit=5)
async def clear_cache_command(message: Message):
    """Очистка кэша"""
    diary_parser.clear_cache()
    await message.answer("✅ Кэш успешно очищен!")

@router.message(Command("refresh"))
@anti_flood(limit=5)
async def refresh_command(message: Message):
    """Принудительное обновление данных (игнорируя кэш)"""
    await message.answer("🔄 Принудительное обновление данных...")
    
    # Очищаем кэш для текущей недели
    diary_parser.clear_cache()
    
    # Получаем свежие данные
    lessons = diary_parser.get_homework_for_today(use_cache=False)
    
    if not lessons:
        await message.answer("❌ Не удалось обновить данные")
        return
        
    await message.answer("✅ Данные успешно обновлены!")
    await dz_today(message)  # Показываем обновленные данные

@router.message(Command("cache_info"))
@anti_flood(limit=5)
async def cache_info_command(message: Message):
    """Информация о кэше"""
    cache_dir = "cache"
    if os.path.exists(cache_dir):
        cache_files = os.listdir(cache_dir)
        cache_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files)
        
        info_text = (
            f"📊 Информация о кэше:\n"
            f"• Файлов в кэше: {len(cache_files)}\n"
            f"• Размер кэша: {cache_size / 1024:.2f} KB\n"
            f"• Время жизни кэша: 1 час\n"
            f"• Статус: {'✅ ВКЛ' if diary_parser.cache_enabled else '❌ ВЫКЛ'}\n\n"
            f"Команды:\n"
            f"/clear_cache - очистить кэш\n"
            f"/refresh - обновить данные\n"
            f"/cache_on - включить кэш\n"
            f"/cache_off - выключить кэш"
        )
    else:
        info_text = "Кэш не инициализирован"
    
    await message.answer(info_text)

@router.message(Command("cache_on"))
@anti_flood(limit=3)
async def cache_on_command(message: Message):
    """Включить кэширование"""
    diary_parser.cache_enabled = True
    await message.answer("✅ Кэширование включено")

@router.message(Command("cache_off"))
@anti_flood(limit=3)
async def cache_off_command(message: Message):
    """Выключить кэширование"""
    diary_parser.cache_enabled = False
    await message.answer("❌ Кэширование выключено")

# Обнови функции ДЗ чтобы использовать кэш по умолчанию
async def dz_today(message: Message, use_cache=True):
    await message.answer("🔄 Получаю домашние задания на сегодня...")
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_today(use_cache=use_cache)
    
    if not lessons:
        await message.answer("🎉 На сегодня домашних заданий нет!")
        return
    
    response = f"📚 Домашние задания на сегодня:\n\n"
    subjects_with_hw = []  # Предметы с домашкой
    
    for i, lesson in enumerate(lessons, 1):
        response += f"🕒 {lesson['time']}\n" if lesson.get('time') else ""
        response += f"📖 {lesson['subject']}\n"
        
        if lesson.get('topic'):
            response += f"📝 Тема: {lesson['topic']}\n"
        
        if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
            response += f"📋 ДЗ: Не задано\n"
        else:
            response += f"📋 Домашние задания:\n"
            for hw_item in lesson['homework_items']:
                if hw_item['text'] != 'Не задано':
                    response += f"   • {hw_item['text']}\n"
                    subjects_with_hw.append(lesson['subject'])
        
        if lesson['files']:
            response += f"📎 Файлов: {len(lesson['files'])}\n"
        
        response += "\n"
    
    # Добавляем пометку об источнике данных
    if use_cache:
        response += "\nℹ️ Данные из кэша (актуальны на последний запрос)"
    else:
        response += "\n🔄 Данные обновлены только что"
    
    await message.answer(response)
    
@router.message(F.text == "❌ Отключить уведомления")
@anti_flood(limit=2)
async def disable_notifications(message: Message):
    user_id = message.from_user.id
    unsubscribe_user(user_id)
    await message.answer(
        "❌ Уведомления отключены!\n\n"
        "Вы больше не будете получать автоматические напоминания о ДЗ",
        reply_markup=kb.notify_kb
    )


