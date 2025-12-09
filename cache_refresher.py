import threading
import time
import logging

logger = logging.getLogger(__name__)

class CacheRefresher:
    def __init__(self, diary_parser, interval_seconds=2700):
        """
        interval_seconds — как часто обновлять кэш.
        2700 секунд = 45 минут.
        """
        self.diary_parser = diary_parser
        self.interval = interval_seconds
        self.running = False
        self.thread = None

    def _refresh_loop(self):
        while self.running:
            try:
                logger.info("🔄 Авто-обновление кэша запущено...")
                # Обновляем кэш недели (week_offset=0)
                self.diary_parser.parse_diary(0, use_cache=False)
                logger.info("✅ Кэш успешно обновлён")
            except Exception as e:
                logger.error(f"❌ Ошибка авто-обновления кэша: {e}")

            time.sleep(self.interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()
        logger.info("✅ Фоновое авто-обновление кэша включено")

    def stop(self):
        self.running = False
        logger.info("⛔ Авто-обновление кэша остановлено")
