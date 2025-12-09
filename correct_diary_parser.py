import requests
from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime, timedelta
import re
import json
import hashlib
from cache_refresher import CacheRefresher

logger = logging.getLogger(__name__)

class CorrectDiaryParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.update({
            'ej_fonts': 'be0f7ec7a1f8432234a8eda8f05b124134125672',
            'ej_fp': 'c5debe1c9ce525bfc5d23ba3450fcd51',
            'ej_id': 'cd647356-6834-4438-96b2-eacfd9b76786',
            'ej_login_esia': '1',
            'jwt_v_2': 'твой_токен_здесь',
            'school_domain': 'mboy14evp'
        })
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.download_dir = "downloaded_files"
        self.cache_dir = "cache"
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_expiry = timedelta(hours=3)
        self.cache_enabled = True

    def update_cookie(self, name, value):
        self.session.cookies.set(name, value)

    def save_cookies(self, filepath="cookies.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.session.cookies.get_dict(), f, ensure_ascii=False, indent=2)

    def load_cookies(self, filepath="cookies.json"):
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            self.session.cookies.update(cookies)

    def cleanup_downloaded_files(self):
        try:
            for filename in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("Папка с загруженными файлами очищена")
        except Exception as e:
            logger.error(f"Ошибка при очистке файлов: {e}")

    def get_cache_key(self, week_offset=0):
        key_data = f"diary_week_{week_offset}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_cache_file_path(self, week_offset=0):
        cache_key = self.get_cache_key(week_offset)
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def save_to_cache(self, data, week_offset=0):
        if not self.cache_enabled:
            return
        try:
            cache_file = self.get_cache_file_path(week_offset)
            cache_data = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'week_offset': week_offset
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Данные сохранены в кэш для недели {week_offset}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {e}")

    def load_from_cache(self, week_offset=0):
        if not self.cache_enabled:
            return None
        try:
            cache_file = self.get_cache_file_path(week_offset)
            if not os.path.exists(cache_file):
                return None
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > self.cache_expiry:
                logger.info("Кэш устарел, требуется обновление")
                return None
            logger.info(f"Данные загружены из кэша для недели {week_offset}")
            return cache_data['data']
        except Exception as e:
            logger.error(f"Ошибка при загрузке из кэша: {e}")
            return None

    def clear_cache(self):
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("Кэш полностью очищен")
        except Exception as e:
            logger.error(f"Ошибка при очистке кэша: {e}")

    def parse_diary(self, week_offset=0, use_cache=True):
        if use_cache:
            cached_data = self.load_from_cache(week_offset)
            if cached_data is not None:
                return cached_data
        try:
            url = f"https://edu.rk.gov.ru/journal-app/u.6417/week.{week_offset}"
            response = self.session.get(url)
            logger.info(f"Status Code: {response.status_code}")
            if "authorize" in response.url:
                logger.error("Ошибка авторизации: неверные куки")
                return None
            parsed_data = self.parse_diary_structure(response.text)
            if parsed_data and use_cache:
                self.save_to_cache(parsed_data, week_offset)
            return parsed_data
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
            if use_cache:
                cached_data = self.load_from_cache(week_offset)
                if cached_data is not None:
                    logger.info("Используем устаревшие данные из кэша из-за ошибки парсинга")
                    return cached_data
            return None

    def parse_diary_structure(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        homework_data = {}
        day_elements = soup.find_all('div', class_='dnevnik-day')
        logger.info(f"Найдено дней: {len(day_elements)}")
        for day_element in day_elements:
            day_info = self.parse_day(day_element)
            if day_info:
                day_name, lessons = day_info
                homework_data[day_name] = lessons
        return homework_data

    def parse_day(self, day_element):
        day_header = day_element.find('div', class_='dnevnik-day__header')
        if not day_header:
            return None
        day_title = day_header.find('div', class_='dnevnik-day__title')
        if not day_title:
            return None
        day_text = day_title.get_text(strip=True)
        day_name = self.extract_day_name(day_text)
        if not day_name:
            return None
        lessons_container = day_element.find('div', class_='dnevnik-day__lessons')
        if not lessons_container:
            return day_name, []
        lessons = []
        lesson_elements = lessons_container.find_all('div', class_='dnevnik-lesson')
        for lesson_element in lesson_elements:
            lesson_data = self.parse_lesson(lesson_element)
            if lesson_data:
                lessons.append(lesson_data)
        return day_name, lessons

    def extract_day_name(self, day_text):
        days_mapping = {
            'понедельник': 'Понедельник',
            'вторник': 'Вторник',
            'среда': 'Среда',
            'четверг': 'Четверг',
            'пятница': 'Пятница',
            'суббота': 'Суббота'
        }
        day_lower = day_text.lower()
        for ru_day, normalized in days_mapping.items():
            if ru_day in day_lower:
                return normalized
        return None

    def parse_lesson(self, lesson_element):
        try:
            subject_element = lesson_element.find('span', class_='js-rt_licey-dnevnik-subject')
            if not subject_element:
                return None
            subject = subject_element.get_text(strip=True)
            if not subject:
                return None
            time_element = lesson_element.find('div', class_='dnevnik-lesson__time')
            lesson_time = time_element.get_text(strip=True) if time_element else ""
            homework_items = self.parse_homework(lesson_element)
            topic_element = lesson_element.find('span', class_='js-rt_licey-dnevnik-topic')
            topic = topic_element.get_text(strip=True) if topic_element else ""
            files = self.parse_attached_files(lesson_element)
            return {
                'subject': subject,
                'homework_items': homework_items,
                'topic': topic,
                'time': lesson_time,
                'files': files
            }
        except Exception as e:
            logger.error(f"Ошибка при парсинге урока: {e}")
            return None

    def parse_homework(self, lesson_element):
        homework_items = []
        task_elements = lesson_element.find_all('div', class_='dnevnik-lesson__task')
        for task_element in task_elements:
            task_text = ""
            for element in task_element.contents:
                if element.name is None:
                    task_text += str(element).strip()
                elif element.name not in ['div', 'a']:
                    task_text += element.get_text(strip=True)
            task_text = self.clean_homework_text(task_text)
            if task_text and task_text.lower() not in ['нет', 'не задано']:
                homework_items.append({
                    'type': 'задание',
                    'text': task_text
                })
        if not homework_items:
            homework_items.append({
                'type': 'задание',
                'text': 'Не задано'
            })
        return homework_items

    def clean_homework_text(self, text):
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^[•\-\*]\s*', '', text)
        return text

    def parse_attached_files(self, lesson_element):
        files = []
        file_links = lesson_element.find_all('a', href=True)
        for link in file_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if (any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.jpg', '.png', '.jpeg', '.zip', '.rar']) or
                any(keyword in text.lower() for keyword in ['.jpg', '.png', '.doc', '.pdf', 'file'])):
                file_url = href
                if not file_url.startswith('http'):
                    file_url = f"https://edu.rk.gov.ru{file_url}"
                file_name = text or os.path.basename(file_url) or f"Файл_{len(files) + 1}"
                files.append({
                    'name': file_name,
                    'url': file_url
                })
        return files

    def download_all_files(self, files):
        downloaded_files = []
        for file_info in files:
            filepath = self.download_file(file_info['url'], file_info['name'])
            if filepath and os.path.exists(filepath):
                downloaded_files.append({
                    'path': filepath,
                    'name': file_info['name'],
                    'original_info': file_info
                })
        return downloaded_files

    def download_file(self, file_url, filename):
        try:
            response = self.session.get(file_url, stream=True)
            if response.status_code == 200:
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                filepath = os.path.join(self.download_dir, safe_filename)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Файл скачан: {safe_filename}")
                return filepath
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {filename}: {e}")
        return None

    def get_homework_for_day(self, day_name, week_offset=0, use_cache=True):
        homework_data = self.parse_diary(week_offset, use_cache)
        if not homework_data:
            return None
        return homework_data.get(day_name, [])

    def get_homework_for_today(self, use_cache=True):
        days_russian = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        today_index = datetime.now().weekday()
        today_name = days_russian[today_index]
        return self.get_homework_for_day(today_name, 0, use_cache)

    def get_homework_for_tomorrow(self, use_cache=True):
        days_russian = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        tomorrow_index = (datetime.now() + timedelta(days=1)).weekday()
        tomorrow_name = days_russian[tomorrow_index]
        return self.get_homework_for_day(tomorrow_name, 0, use_cache)

# Глобальный экземпляр парсера
diary_parser = CorrectDiaryParser()

# Авто-обновление каждые 45 минут (2700 секунд)
cache_refresher = CacheRefresher(diary_parser, interval_seconds=2700)
cache_refresher.start()

