import asyncio
import time
from aiogram import Bot
from config import TOKEN
from correct_diary_parser import diary_parser

bot = Bot(token=TOKEN)

subscribed_users = set()

NOTIFY_HOUR = 17
NOTIFY_MINUTE = 0  # 🔧 теперь легко менять

async def check_and_send_homework_reminders():
    while True:
        current_time = time.localtime()
        if current_time.tm_hour == NOTIFY_HOUR and current_time.tm_min == NOTIFY_MINUTE:
            await send_daily_reminders()
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(60)

async def send_daily_reminders():
    if not subscribed_users:
        return
    diary_parser.cleanup_downloaded_files()
    lessons = diary_parser.get_homework_for_tomorrow()

    if not lessons:
        message_text = "🎉 На завтра домашних заданий нет! Хорошего отдыха! ✨"
    else:
        message_text = "📚 Напоминание о домашних заданиях на завтра:\n\n"
        
        for i, lesson in enumerate(lessons, 1):
            message_text += f"📖 {lesson['subject']}\n"
            
            if len(lesson['homework_items']) == 1 and lesson['homework_items'][0]['text'] == 'Не задано':
                message_text += f"   ✅ Не задано\n"
            else:
                for hw_item in lesson['homework_items']:
                    if hw_item['text'] != 'Не задано':
                        message_text += f"   • {hw_item['text']}\n"
            
            message_text += "\n"
        
        message_text += "⏰ Удачи в выполнении! 💪"
    
    # Отправляем всем подписанным пользователям
    for user_id in subscribed_users.copy():
        try:
            await bot.send_message(user_id, message_text)
            await asyncio.sleep(0.1)  # Небольшая задержка
        except Exception as e:
            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
            subscribed_users.discard(user_id)

def subscribe_user(user_id: int):
    """Добавляет пользователя в список для уведомлений"""
    subscribed_users.add(user_id)

def unsubscribe_user(user_id: int):
    """Удаляет пользователя из списка уведомлений"""
    subscribed_users.discard(user_id)

def is_subscribed(user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на уведомления"""
    return user_id in subscribed_users