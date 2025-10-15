"""
Виджет чата для отображения сообщений
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QScrollArea, 
    QLabel, QFrame, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor, QPixmap, QColor, QPalette
from datetime import datetime
from typing import Optional


class MessageWidget(QFrame):
    """Виджет для отображения одного сообщения"""
    
    def __init__(self, message: str, sender: str, timestamp: Optional[datetime] = None):
        super().__init__()
        self.message = message
        self.sender = sender
        self.timestamp = timestamp or datetime.now()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса сообщения"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Заголовок с именем отправителя и временем
        header_layout = QHBoxLayout()
        
        sender_label = QLabel(self.sender)
        sender_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        time_label = QLabel(self.timestamp.strftime("%H:%M"))
        time_label.setFont(QFont("Arial", 9))
        time_label.setStyleSheet("color: #888888;")
        
        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Текст сообщения
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 11))
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        layout.addWidget(message_label)
        
        # Стиль в зависимости от отправителя
        self.apply_style()
    
    def apply_style(self):
        """Применение стиля в зависимости от отправителя"""
        if self.sender == "Вы":
            # Сообщения пользователя - справа, синий фон
            self.setStyleSheet("""
                MessageWidget {
                    background-color: #1976D2;
                    color: white;
                    border-radius: 10px;
                    margin-left: 50px;
                    margin-right: 10px;
                }
            """)
        elif self.sender == "Сакура":
            # Сообщения ИИ - слева, фиолетовый фон
            self.setStyleSheet("""
                MessageWidget {
                    background-color: #7B1FA2;
                    color: white;
                    border-radius: 10px;
                    margin-left: 10px;
                    margin-right: 50px;
                }
            """)
        elif self.sender == "Система":
            # Системные сообщения - центр, серый фон
            self.setStyleSheet("""
                MessageWidget {
                    background-color: #424242;
                    color: #CCCCCC;
                    border-radius: 8px;
                    margin-left: 30px;
                    margin-right: 30px;
                    font-style: italic;
                }
            """)
        else:
            # Ошибки - красный фон
            self.setStyleSheet("""
                MessageWidget {
                    background-color: #D32F2F;
                    color: white;
                    border-radius: 8px;
                    margin-left: 20px;
                    margin-right: 20px;
                }
            """)


class ChatWidget(QWidget):
    """Виджет чата с прокруткой"""
    
    message_sent = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self.setup_ui()
        
        # Таймер для автопрокрутки
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.scroll_to_bottom)
    
    def setup_ui(self):
        """Настройка интерфейса чата"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Область прокрутки
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Контейнер для сообщений
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Стиль
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
            }
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #707070;
            }
        """)
        
        # Приветственное сообщение
        self.add_system_message("Привет! Я Сакура, твоя виртуальная вайфу-геймер! 🌸\nМожешь писать мне текстом или говорить в микрофон!")
    
    def add_message(self, message: str, sender: str, timestamp: Optional[datetime] = None):
        """Добавление сообщения в чат"""
        message_widget = MessageWidget(message, sender, timestamp)
        self.messages_layout.addWidget(message_widget)
        self.messages.append(message_widget)
        
        # Автопрокрутка
        self.scroll_timer.start(100)
        
        # Ограничение количества сообщений (для производительности)
        max_messages = 1000
        if len(self.messages) > max_messages:
            old_message = self.messages.pop(0)
            old_message.deleteLater()
    
    def add_user_message(self, message: str):
        """Добавление сообщения пользователя"""
        self.add_message(message, "Вы")
    
    def add_assistant_message(self, message: str):
        """Добавление сообщения ИИ"""
        self.add_message(message, "Сакура")
    
    def add_system_message(self, message: str):
        """Добавление системного сообщения"""
        self.add_message(message, "Система")
    
    def add_error_message(self, message: str):
        """Добавление сообщения об ошибке"""
        self.add_message(message, "Ошибка")
    
    def scroll_to_bottom(self):
        """Прокрутка к последнему сообщению"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear(self):
        """Очистка чата"""
        # Удаляем все виджеты сообщений
        for message in self.messages:
            message.deleteLater()
        
        self.messages.clear()
        
        # Добавляем сообщение о очистке
        self.add_system_message("Чат очищен")
    
    def export_to_text(self) -> str:
        """Экспорт чата в текстовый формат"""
        lines = []
        for message_widget in self.messages:
            timestamp_str = message_widget.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[{timestamp_str}] {message_widget.sender}: {message_widget.message}")
        
        return "\n".join(lines)
    
    def get_message_count(self) -> int:
        """Получение количества сообщений"""
        return len(self.messages)
    
    def get_last_messages(self, count: int = 10) -> list:
        """Получение последних сообщений"""
        return self.messages[-count:] if count <= len(self.messages) else self.messages
    
    def find_messages(self, query: str) -> list:
        """Поиск сообщений по тексту"""
        found_messages = []
        query_lower = query.lower()
        
        for message_widget in self.messages:
            if query_lower in message_widget.message.lower():
                found_messages.append(message_widget)
        
        return found_messages
    
    def highlight_message(self, message_widget: MessageWidget):
        """Подсветка сообщения"""
        # Сохраняем оригинальный стиль
        original_style = message_widget.styleSheet()
        
        # Применяем подсветку
        message_widget.setStyleSheet(original_style + """
            border: 2px solid #FFC107;
        """)
        
        # Убираем подсветку через 2 секунды
        QTimer.singleShot(2000, lambda: message_widget.setStyleSheet(original_style))
        
        # Прокручиваем к сообщению
        self.scroll_area.ensureWidgetVisible(message_widget)
