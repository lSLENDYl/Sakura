#!/usr/bin/env python3
"""
Главный файл приложения Sakura AI
Виртуальная вайфу-геймер с ИИ персонажем
"""

import sys
import os
import asyncio
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from config.config_manager import config
from utils.logger import setup_logger, logger


class SakuraAIApplication:
    """Главный класс приложения"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.splash = None
        
    def setup_application(self):
        """Настройка приложения"""
        # Создание QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Sakura AI")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("SakuraAI")
        
        # Настройка логирования
        log_level = config.get('logging.level', 'INFO')
        log_file = config.get('logging.file', 'logs/sakura_ai.log')
        global logger
        logger = setup_logger("SakuraAI", log_level, log_file)
        
        logger.info("=" * 50)
        logger.info("Запуск Sakura AI")
        logger.info("=" * 50)
        
        # Проверка системных требований
        if not self.check_requirements():
            return False
        
        # Создание splash screen
        self.create_splash()
        
        return True
    
    def check_requirements(self) -> bool:
        """Проверка системных требований"""
        logger.info("Проверка системных требований...")
        
        # Проверка Python версии
        if sys.version_info < (3, 8):
            QMessageBox.critical(
                None, 
                "Ошибка",
                f"Требуется Python 3.8 или выше.\nТекущая версия: {sys.version}"
            )
            return False
        
        # Проверка PyQt5
        try:
            from PyQt5.QtCore import QT_VERSION_STR
            logger.info(f"PyQt5 версия: {QT_VERSION_STR}")
        except ImportError:
            QMessageBox.critical(
                None,
                "Ошибка", 
                "PyQt5 не установлен.\nУстановите: pip install PyQt5"
            )
            return False
        
        # Проверка других зависимостей
        required_modules = [
            ('torch', 'PyTorch'),
            ('ollama', 'Ollama Python client'),
            ('vosk', 'Vosk'),
            ('pyaudio', 'PyAudio'),
            ('sounddevice', 'SoundDevice')
        ]
        
        missing_modules = []
        for module_name, display_name in required_modules:
            try:
                __import__(module_name)
                logger.info(f"✓ {display_name}")
            except ImportError:
                logger.error(f"✗ {display_name}")
                missing_modules.append(display_name)
        
        if missing_modules:
            QMessageBox.critical(
                None,
                "Отсутствуют зависимости",
                f"Не установлены следующие модули:\n" + 
                "\n".join(f"- {module}" for module in missing_modules) +
                "\n\nУстановите их с помощью:\npip install -r requirements.txt"
            )
            return False
        
        logger.info("Все системные требования выполнены")
        return True
    
    def create_splash(self):
        """Создание splash screen"""
        try:
            # Создаем простой splash screen
            splash_pixmap = QPixmap(400, 300)
            splash_pixmap.fill(Qt.black)
            
            self.splash = QSplashScreen(splash_pixmap)
            self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            
            # Добавляем текст
            self.splash.showMessage(
                "🌸 Sakura AI\n\nЗагрузка...\n\nВиртуальная вайфу-геймер",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.white
            )
            
            self.splash.show()
            self.app.processEvents()
            
        except Exception as e:
            logger.warning(f"Не удалось создать splash screen: {e}")
    
    def initialize_components(self):
        """Инициализация компонентов приложения"""
        try:
            if self.splash:
                self.splash.showMessage(
                    "🌸 Sakura AI\n\nИнициализация компонентов...",
                    Qt.AlignCenter | Qt.AlignBottom,
                    Qt.white
                )
                self.app.processEvents()
            
            # Создание главного окна
            logger.info("Создание главного окна...")
            self.main_window = MainWindow()
            
            if self.splash:
                self.splash.showMessage(
                    "🌸 Sakura AI\n\nПочти готово...",
                    Qt.AlignCenter | Qt.AlignBottom,
                    Qt.white
                )
                self.app.processEvents()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            QMessageBox.critical(
                None,
                "Ошибка инициализации",
                f"Не удалось инициализировать приложение:\n{e}"
            )
            return False
    
    def show_main_window(self):
        """Показ главного окна"""
        try:
            # Скрываем splash screen
            if self.splash:
                QTimer.singleShot(1000, self.splash.close)
            
            # Показываем главное окно
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            logger.info("Главное окно отображено")
            
        except Exception as e:
            logger.error(f"Ошибка показа главного окна: {e}")
    
    def run(self):
        """Запуск приложения"""
        if not self.setup_application():
            return 1
        
        if not self.initialize_components():
            return 1
        
        # Показываем главное окно через небольшую задержку
        QTimer.singleShot(2000, self.show_main_window)
        
        # Запуск главного цикла
        logger.info("Запуск главного цикла приложения")
        try:
            exit_code = self.app.exec_()
            logger.info(f"Приложение завершено с кодом: {exit_code}")
            return exit_code
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
            return 0
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            return 1


def main():
    """Точка входа в приложение"""
    try:
        # Создание и запуск приложения
        app = SakuraAIApplication()
        return app.run()
        
    except Exception as e:
        print(f"Критическая ошибка запуска: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
