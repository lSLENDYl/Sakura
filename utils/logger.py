"""
Настройки логирования для приложения Sakura AI
"""

import os
import logging
import logging.handlers
from typing import Optional
from colorlog import ColoredFormatter


def setup_logger(name: str = "SakuraAI", level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Настраивает логгер с цветным выводом в консоль и опциональным файлом
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Если уже настроен, возвращаем существующий
    if logger.handlers:
        return logger
    
    # Цветной форматтер для консоли
    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Файловый хендлер (опционально)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Ротация файлов (10MB, 5 бэкапов)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Глобальный логгер
logger = setup_logger()
