"""
Главное окно приложения Sakura AI
"""

import sys
import asyncio
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QMenuBar, 
    QStatusBar, QSplitter, QMessageBox, QLabel,
    QProgressBar, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap

from .settings_dialog import SettingsDialog
from .widgets.chat_widget import ChatWidget
from ai.ollama_client import OllamaClient
from tts.silero_tts import SileroTTS
from stt.vosk_stt import VoskSTT
from config.config_manager import config
from utils.logger import logger


class ResponseThread(QThread):
    """Поток для генерации ответов ИИ"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ollama_client: OllamaClient, user_input: str):
        super().__init__()
        self.ollama_client = ollama_client
        self.user_input = user_input
    
    def run(self):
        try:
            response = self.ollama_client.generate_response(self.user_input)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        
        # Инициализация компонентов
        self.ollama_client = OllamaClient()
        self.tts = SileroTTS()
        self.stt = VoskSTT()
        
        # Состояние приложения
        self.is_listening = False
        self.is_muted = False
        self.current_response_thread: Optional[ResponseThread] = None
        
        # Настройка окна
        self.setup_ui()
        self.setup_connections()
        self.setup_system_tray()
        self.load_settings()
        
        # Проверка готовности компонентов
        QTimer.singleShot(1000, self.check_components)
        
        logger.info("Главное окно инициализировано")
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Sakura AI - Виртуальная Вайфу")
        self.setMinimumSize(800, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Виджет чата
        self.chat_widget = ChatWidget()
        main_layout.addWidget(self.chat_widget)
        
        # Панель ввода
        input_layout = QHBoxLayout()
        
        # Поле ввода
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Напиши что-нибудь Сакуре...")
        self.input_field.setFont(QFont("Arial", 12))
        self.input_field.setMinimumHeight(40)
        input_layout.addWidget(self.input_field, stretch=1)
        
        # Кнопка отправки
        self.send_button = QPushButton("Отправить")
        self.send_button.setMinimumSize(100, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        input_layout.addWidget(self.send_button)
        
        main_layout.addLayout(input_layout)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        # Кнопка микрофона
        self.mic_button = QPushButton("🎤 Слушать")
        self.mic_button.setMinimumSize(120, 35)
        self.mic_button.setCheckable(True)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
        """)
        control_layout.addWidget(self.mic_button)
        
        # Кнопка заглушения
        self.mute_button = QPushButton("🔊 Звук")
        self.mute_button.setMinimumSize(100, 35)
        self.mute_button.setCheckable(True)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
        """)
        control_layout.addWidget(self.mute_button)
        
        # Кнопка очистки истории
        self.clear_button = QPushButton("🗑️ Очистить")
        self.clear_button.setMinimumSize(100, 35)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        control_layout.addWidget(self.clear_button)
        
        # Кнопка настроек
        self.settings_button = QPushButton("⚙️ Настройки")
        self.settings_button.setMinimumSize(100, 35)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        control_layout.addWidget(self.settings_button)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Индикатор состояния
        self.status_label = QLabel("Готов")
        self.status_bar.addWidget(self.status_label)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Меню
        self.setup_menu()
    
    def setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        export_action = QAction("Экспорт чата", self)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        
        preferences_action = QAction("Настройки", self)
        preferences_action.triggered.connect(self.show_settings)
        settings_menu.addAction(preferences_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Настройка соединений сигналов и слотов"""
        # Поле ввода
        self.input_field.returnPressed.connect(self.send_message)
        
        # Кнопки
        self.send_button.clicked.connect(self.send_message)
        self.mic_button.clicked.connect(self.toggle_listening)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.clear_button.clicked.connect(self.clear_history)
        self.settings_button.clicked.connect(self.show_settings)
        
        # STT callbacks
        self.stt.set_callbacks(
            on_partial=self.on_partial_speech,
            on_final=self.on_final_speech,
            on_error=self.on_speech_error
        )
    
    def setup_system_tray(self):
        """Настройка системного трея"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Меню трея
            tray_menu = QMenu()
            
            show_action = QAction("Показать", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("Выход", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
    
    def load_settings(self):
        """Загрузка настроек"""
        # Размер и позиция окна
        window_size = config.get('gui.window_size', [800, 600])
        window_pos = config.get('gui.window_position', [100, 100])
        
        self.resize(window_size[0], window_size[1])
        self.move(window_pos[0], window_pos[1])
        
        # Тема
        theme = config.get('gui.theme', 'dark')
        self.apply_theme(theme)
    
    def apply_theme(self, theme: str):
        """Применение темы"""
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px;
                }
                QStatusBar {
                    background-color: #353535;
                    color: #ffffff;
                }
            """)
    
    def check_components(self):
        """Проверка готовности компонентов"""
        status_parts = []
        
        # Проверка Ollama
        if self.ollama_client.is_available():
            status_parts.append("AI ✓")
        else:
            status_parts.append("AI ✗")
        
        # Проверка TTS
        if self.tts.is_available():
            status_parts.append("TTS ✓")
        else:
            status_parts.append("TTS ✗")
        
        # Проверка STT
        if self.stt.is_available():
            status_parts.append("STT ✓")
        else:
            status_parts.append("STT ✗")
        
        status_text = " | ".join(status_parts)
        self.status_label.setText(status_text)
        
        # Если все компоненты готовы
        if all("✓" in part for part in status_parts):
            self.chat_widget.add_system_message("Сакура готова к общению! 🌸")
    
    def send_message(self):
        """Отправка сообщения"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Очистка поля ввода
        self.input_field.clear()
        
        # Добавление сообщения пользователя
        self.chat_widget.add_user_message(text)
        
        # Отправка запроса ИИ
        self.process_user_input(text)
    
    def process_user_input(self, text: str):
        """Обработка пользовательского ввода"""
        if not self.ollama_client.is_available():
            self.chat_widget.add_error_message("ИИ недоступен")
            return
        
        # Показать прогресс
        self.progress_bar.setVisible(True)
        self.status_label.setText("Сакура думает...")
        
        # Запуск потока генерации ответа
        self.current_response_thread = ResponseThread(self.ollama_client, text)
        self.current_response_thread.response_ready.connect(self.on_response_ready)
        self.current_response_thread.error_occurred.connect(self.on_response_error)
        self.current_response_thread.start()
    
    def on_response_ready(self, response: str):
        """Обработка готового ответа"""
        # Скрыть прогресс
        self.progress_bar.setVisible(False)
        self.status_label.setText("Готов")
        
        # Добавить ответ в чат
        self.chat_widget.add_assistant_message(response)
        
        # Озвучить ответ (если не заглушено)
        if not self.is_muted and self.tts.is_available():
            self.tts.speak(response)
        
        self.current_response_thread = None
    
    def on_response_error(self, error: str):
        """Обработка ошибки генерации ответа"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ошибка")
        
        self.chat_widget.add_error_message(f"Ошибка: {error}")
        self.current_response_thread = None
    
    def toggle_listening(self):
        """Переключение прослушивания"""
        if not self.stt.is_available():
            QMessageBox.warning(self, "Ошибка", "Распознавание речи недоступно")
            self.mic_button.setChecked(False)
            return
        
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Начать прослушивание"""
        if self.stt.start_listening():
            self.is_listening = True
            self.mic_button.setText("🎤 Остановить")
            self.status_label.setText("Слушаю...")
            self.chat_widget.add_system_message("Начинаю слушать...")
        else:
            self.mic_button.setChecked(False)
            QMessageBox.warning(self, "Ошибка", "Не удалось начать прослушивание")
    
    def stop_listening(self):
        """Остановить прослушивание"""
        self.stt.stop_listening()
        self.is_listening = False
        self.mic_button.setText("🎤 Слушать")
        self.status_label.setText("Готов")
    
    def toggle_mute(self):
        """Переключение звука"""
        self.is_muted = self.mute_button.isChecked()
        
        if self.is_muted:
            self.mute_button.setText("🔇 Заглушено")
            self.tts.stop()
        else:
            self.mute_button.setText("🔊 Звук")
    
    def clear_history(self):
        """Очистка истории"""
        reply = QMessageBox.question(
            self, 
            "Очистка истории", 
            "Вы уверены, что хотите очистить всю историю разговора?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.chat_widget.clear()
            self.ollama_client.clear_history()
            self.chat_widget.add_system_message("История очищена")
    
    def show_settings(self):
        """Показать настройки"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == dialog.Accepted:
            # Перезагрузить настройки
            self.load_settings()
    
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            self,
            "О программе",
            """
            <h3>Sakura AI</h3>
            <p>Виртуальная вайфу-геймер с ИИ</p>
            <p><b>Возможности:</b></p>
            <ul>
                <li>Общение с ИИ персонажем</li>
                <li>Синтез речи (Silero TTS)</li>
                <li>Распознавание речи (Vosk)</li>
                <li>Настраиваемая личность</li>
            </ul>
            <p><b>Технологии:</b> Python, PyQt5, Ollama, Silero, Vosk</p>
            """
        )
    
    def on_partial_speech(self, text: str):
        """Обработка частичного результата распознавания"""
        if text:
            self.status_label.setText(f"Слышу: {text}")
    
    def on_final_speech(self, text: str):
        """Обработка финального результата распознавания"""
        if text:
            logger.info(f"Распознана речь: {text}")
            self.input_field.setText(text)
            self.send_message()
    
    def on_speech_error(self, error: str):
        """Обработка ошибки распознавания"""
        logger.error(f"Ошибка распознавания речи: {error}")
        self.status_label.setText("Ошибка распознавания")
    
    def on_tray_activated(self, reason):
        """Обработка активации трея"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if config.get('gui.minimize_to_tray', True) and hasattr(self, 'tray_icon'):
            event.ignore()
            self.hide()
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage(
                    "Sakura AI",
                    "Приложение свернуто в трей",
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            # Сохранить настройки окна
            config.set('gui.window_size', [self.width(), self.height()])
            config.set('gui.window_position', [self.x(), self.y()])
            
            # Остановить компоненты
            if self.is_listening:
                self.stop_listening()
            
            if self.current_response_thread:
                self.current_response_thread.wait()
            
            event.accept()
