import logging
from datetime import datetime

def setup_logger():
    aiogram_logger = logging.getLogger('aiogram')
    aiogram_logger.setLevel(logging.WARNING)
    file_log = logging.FileHandler(f'./logs/LOG_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log', encoding='utf-8')
    console_out = logging.StreamHandler()
    logging.basicConfig(
        level=logging.INFO,
        handlers=(file_log, console_out),
        format='[%(asctime)s][%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.addLevelName(logging.INFO, "Информация")
    logging.addLevelName(logging.DEBUG, "Отладка")
    logging.addLevelName(logging.WARNING, "Предупреждение")
    logging.addLevelName(logging.ERROR, "Ошибка")
    logging.addLevelName(logging.CRITICAL, "Критическая ошибка")

logger = logging.getLogger()