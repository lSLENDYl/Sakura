"""
Диалог настроек приложения
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QSpinBox, 
    QDoubleSpinBox, QComboBox, QCheckBox, QSlider,
    QTextEdit, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QProgressBar, QListWidget, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from config.config_manager import config
from .widgets.settings_tabs import PersonalityTab, ModulesTab, GeneralTab
from utils.logger import logger


class SettingsDialog(QDialog):
    """Диалог настроек приложения"""

    # НОВЫЙ СИГНАЛ: Уведомление об изменении настроек
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки Sakura AI")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        # Сохраняем ссылку на главное окно для применения настроек
        self.main_window = parent

        # Сохраняем оригинальную конфигурацию для отмены
        self.original_config = config.config.copy()

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)

        # Вкладки
        self.tab_widget = QTabWidget()

        # Вкладка "Общие"
        self.general_tab = GeneralTab()
        self.tab_widget.addTab(self.general_tab, "Общие")

        # Вкладка "Личность ИИ"
        self.personality_tab = PersonalityTab()
        self.tab_widget.addTab(self.personality_tab, "Личность ИИ")

        # Вкладка "Модули"
        self.modules_tab = ModulesTab()
        self.tab_widget.addTab(self.modules_tab, "Модули")

        layout.addWidget(self.tab_widget)

        # Кнопки
        button_layout = QHBoxLayout()

        # Кнопка "По умолчанию"
        self.reset_button = QPushButton("По умолчанию")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        # НОВАЯ КНОПКА: Применить без закрытия
        self.apply_button = QPushButton("Применить")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        button_layout.addStretch()

        # Кнопка "Отмена"
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # Кнопка "ОК" 
        self.ok_button = QPushButton("ОК")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # Стиль
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1976D2;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)

    def load_settings(self):
        """Загрузка текущих настроек"""
        self.general_tab.load_settings()
        self.personality_tab.load_settings()
        self.modules_tab.load_settings()

    def save_settings(self):
        """Сохранение настроек"""
        try:
            self.general_tab.save_settings()
            self.personality_tab.save_settings()
            self.modules_tab.save_settings()

            logger.info("Настройки сохранены")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки:\n{e}")
            return False

    def apply_settings(self):
        """НОВЫЙ МЕТОД: Применение настроек без закрытия диалога"""
        if self.save_settings():
            self.apply_to_components()
            QMessageBox.information(self, "Готово", "Настройки применены!")

    def accept_settings(self):
        """Принятие настроек"""
        if self.save_settings():
            self.apply_to_components()
            self.accept()

    def apply_to_components(self):
        """НОВЫЙ МЕТОД: Применение настроек к компонентам приложения"""
        if not self.main_window:
            return

        try:
            logger.info("Применение настроек к компонентам...")

            # Применяем настройки к компонентам главного окна
            self.apply_ollama_settings()
            self.apply_tts_settings()
            self.apply_stt_settings()
            self.apply_gui_settings()

            # Уведомляем главное окно об изменениях
            self.settings_changed.emit()

            logger.info("Настройки применены к компонентам")

        except Exception as e:
            logger.error(f"Ошибка применения настроек: {e}")
            QMessageBox.warning(self, "Предупреждение", 
                              f"Настройки сохранены, но не все изменения применены:\n{e}\n\nПерезапустите приложение для полного применения.")

    def apply_ollama_settings(self):
        """Применяет настройки Ollama"""
        try:
            ollama_client = self.main_window.ollama_client

            # Обновляем настройки клиента
            ollama_client.host = config.get('ai.ollama_host', 'http://localhost:11434')
            new_model = config.get('ai.model', 'qwen3:30b')

            # Если модель изменилась, обновляем её
            if ollama_client.model != new_model:
                if ollama_client.set_model(new_model):
                    logger.info(f"Модель Ollama изменена на: {new_model}")
                else:
                    logger.warning(f"Не удалось сменить модель на: {new_model}")

            # Обновляем системный промпт
            ollama_client.system_prompt = config.get('personality.system_prompt', '')

        except Exception as e:
            logger.error(f"Ошибка применения настроек Ollama: {e}")

    def apply_tts_settings(self):
        """Применяет настройки TTS"""
        try:
            tts = self.main_window.tts

            # Обновляем настройки TTS
            new_speaker = config.get('tts.speaker', 'baya')
            if tts.speaker != new_speaker:
                tts.set_speaker(new_speaker)

            tts.set_volume(config.get('tts.volume', 0.8))
            tts.set_speed(config.get('tts.speed', 1.0))

            logger.info("Настройки TTS применены")

        except Exception as e:
            logger.error(f"Ошибка применения настроек TTS: {e}")

    def apply_stt_settings(self):
        """Применяет настройки STT"""
        try:
            stt = self.main_window.stt

            # Для STT изменения требуют перезапуска компонента
            # Пока просто логируем
            logger.info("Настройки STT сохранены (требуется перезапуск для применения)")

        except Exception as e:
            logger.error(f"Ошибка применения настроек STT: {e}")

    def apply_gui_settings(self):
        """Применяет настройки интерфейса"""
        try:
            # Применяем тему
            theme = config.get('gui.theme', 'dark')
            self.main_window.apply_theme(theme)

            # Применяем настройки окна
            always_on_top = config.get('gui.always_on_top', False)
            if always_on_top:
                self.main_window.setWindowFlags(self.main_window.windowFlags() | Qt.WindowStaysOnTopHint)
            else:
                self.main_window.setWindowFlags(self.main_window.windowFlags() & ~Qt.WindowStaysOnTopHint)

            self.main_window.show()  # Применяем флаги окна

            logger.info("Настройки интерфейса применены")

        except Exception as e:
            logger.error(f"Ошибка применения настроек интерфейса: {e}")

    def reject(self):
        """Отмена настроек"""
        # Восстанавливаем оригинальную конфигурацию
        config.config = self.original_config
        super().reject()

    def reset_to_defaults(self):
        """Сброс к настройкам по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Сброс настроек",
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            config.reset_to_default()
            self.load_settings()
            QMessageBox.information(self, "Готово", "Настройки сброшены к значениям по умолчанию")
