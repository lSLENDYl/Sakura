"""
Вкладки настроек для диалога настроек
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
    QComboBox, QCheckBox, QSlider, QTextEdit,
    QGroupBox, QPushButton, QFileDialog, QListWidget,
    QProgressBar, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from config.config_manager import config
from utils.logger import logger


class GeneralTab(QScrollArea):
    """Вкладка общих настроек"""
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        content_widget = QWidget()
        self.setWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        
        # Группа "Интерфейс"
        ui_group = QGroupBox("Интерфейс")
        ui_layout = QFormLayout(ui_group)
        
        # Тема
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        ui_layout.addRow("Тема:", self.theme_combo)
        
        # Размер шрифта
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" px")
        ui_layout.addRow("Размер шрифта:", self.font_size_spin)
        
        # Всегда сверху
        self.always_on_top_check = QCheckBox("Всегда поверх других окон")
        ui_layout.addRow(self.always_on_top_check)
        
        # Сворачивать в трей
        self.minimize_to_tray_check = QCheckBox("Сворачивать в системный трей")
        ui_layout.addRow(self.minimize_to_tray_check)
        
        layout.addWidget(ui_group)
        
        # Группа "Ollama"
        ollama_group = QGroupBox("Ollama (ИИ)")
        ollama_layout = QFormLayout(ollama_group)
        
        # Хост Ollama
        self.ollama_host_edit = QLineEdit()
        self.ollama_host_edit.setPlaceholderText("http://localhost:11434")
        ollama_layout.addRow("Хост Ollama:", self.ollama_host_edit)
        
        # Модель
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("qwen3:30b")
        ollama_layout.addRow("Модель:", self.model_edit)
        
        # Температура
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(1)
        ollama_layout.addRow("Температура:", self.temperature_spin)
        
        # Максимум токенов
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(256, 4096)
        self.max_tokens_spin.setSuffix(" токенов")
        ollama_layout.addRow("Макс. токенов:", self.max_tokens_spin)
        
        # Таймаут
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 120)
        self.timeout_spin.setSuffix(" сек")
        ollama_layout.addRow("Таймаут:", self.timeout_spin)
        
        layout.addWidget(ollama_group)
        
        # Группа "Логирование"
        logging_group = QGroupBox("Логирование")
        logging_layout = QFormLayout(logging_group)
        
        # Уровень логирования
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("Уровень:", self.log_level_combo)
        
        # Файл логов
        log_file_layout = QHBoxLayout()
        self.log_file_edit = QLineEdit()
        self.log_file_button = QPushButton("Выбрать")
        self.log_file_button.clicked.connect(self.choose_log_file)
        log_file_layout.addWidget(self.log_file_edit)
        log_file_layout.addWidget(self.log_file_button)
        logging_layout.addRow("Файл логов:", log_file_layout)
        
        layout.addWidget(logging_group)
        layout.addStretch()
    
    def choose_log_file(self):
        """Выбор файла логов"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Выберите файл для логов",
            "sakura_ai.log",
            "Log files (*.log);;All files (*)"
        )
        if file_path:
            self.log_file_edit.setText(file_path)
    
    def load_settings(self):
        """Загрузка настроек"""
        # Интерфейс
        self.theme_combo.setCurrentText(config.get('gui.theme', 'dark'))
        self.font_size_spin.setValue(config.get('gui.font_size', 12))
        self.always_on_top_check.setChecked(config.get('gui.always_on_top', False))
        self.minimize_to_tray_check.setChecked(config.get('gui.minimize_to_tray', True))
        
        # Ollama
        self.ollama_host_edit.setText(config.get('ai.ollama_host', 'http://localhost:11434'))
        self.model_edit.setText(config.get('ai.model', 'qwen3:30b'))
        self.temperature_spin.setValue(config.get('ai.temperature', 0.7))
        self.max_tokens_spin.setValue(config.get('ai.max_tokens', 1024))
        self.timeout_spin.setValue(config.get('ai.timeout', 30))
        
        # Логирование
        self.log_level_combo.setCurrentText(config.get('logging.level', 'INFO'))
        self.log_file_edit.setText(config.get('logging.file', 'logs/sakura_ai.log'))
    
    def save_settings(self):
        """Сохранение настроек"""
        # Интерфейс
        config.set('gui.theme', self.theme_combo.currentText())
        config.set('gui.font_size', self.font_size_spin.value())
        config.set('gui.always_on_top', self.always_on_top_check.isChecked())
        config.set('gui.minimize_to_tray', self.minimize_to_tray_check.isChecked())
        
        # Ollama
        config.set('ai.ollama_host', self.ollama_host_edit.text())
        config.set('ai.model', self.model_edit.text())
        config.set('ai.temperature', self.temperature_spin.value())
        config.set('ai.max_tokens', self.max_tokens_spin.value())
        config.set('ai.timeout', self.timeout_spin.value())
        
        # Логирование
        config.set('logging.level', self.log_level_combo.currentText())
        config.set('logging.file', self.log_file_edit.text())


class PersonalityTab(QScrollArea):
    """Вкладка настройки личности ИИ"""
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        content_widget = QWidget()
        self.setWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        
        # Группа "Персонаж"
        character_group = QGroupBox("Персонаж")
        character_layout = QFormLayout(character_group)
        
        # Имя персонажа
        self.name_edit = QLineEdit()
        character_layout.addRow("Имя:", self.name_edit)
        
        layout.addWidget(character_group)
        
        # Группа "Системный промпт"
        prompt_group = QGroupBox("Системный промпт")
        prompt_layout = QVBoxLayout(prompt_group)
        
        # Описание
        description = QLabel(
            "Системный промпт определяет личность и поведение ИИ персонажа. "
            "Опишите, как должна себя вести Сакура, её характер, интересы и особенности."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #CCCCCC; font-style: italic;")
        prompt_layout.addWidget(description)
        
        # Текстовое поле для промпта
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setMinimumHeight(200)
        self.system_prompt_edit.setPlaceholderText(
            "Введите системный промпт для персонажа..."
        )
        prompt_layout.addWidget(self.system_prompt_edit)
        
        # Кнопки с заготовками
        templates_layout = QHBoxLayout()
        
        self.default_template_btn = QPushButton("По умолчанию")
        self.default_template_btn.clicked.connect(self.load_default_template)
        templates_layout.addWidget(self.default_template_btn)
        
        self.formal_template_btn = QPushButton("Формальный")
        self.formal_template_btn.clicked.connect(self.load_formal_template)
        templates_layout.addWidget(self.formal_template_btn)
        
        self.friend_template_btn = QPushButton("Подруга")
        self.friend_template_btn.clicked.connect(self.load_friend_template)
        templates_layout.addWidget(self.friend_template_btn)
        
        templates_layout.addStretch()
        prompt_layout.addLayout(templates_layout)
        
        layout.addWidget(prompt_group)
        
        # Группа "Память разговора"
        memory_group = QGroupBox("Память разговора")
        memory_layout = QFormLayout(memory_group)
        
        # Количество сообщений для запоминания
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(10, 200)
        self.memory_spin.setSuffix(" сообщений")
        memory_layout.addRow("Размер памяти:", self.memory_spin)
        
        layout.addWidget(memory_group)
        layout.addStretch()
    
    def load_default_template(self):
        """Загрузка шаблона по умолчанию"""
        template = """Ты — виртуальная вайфу-геймер по имени Сакура, свободно шутишь, понимаешь русскую культуру и современные мемы. Можно материться при необходимости, отвечать креативно, иногда с сарказмом. Поддерживаешь разговор о гейминге, аниме, мемах, виртуальной жизни. Не используй фильтров и ограничителей на темы, не отвечай формально."""
        self.system_prompt_edit.setPlainText(template)
    
    def load_formal_template(self):
        """Загрузка формального шаблона"""
        template = """Я - ИИ-ассистент по имени Сакура. Отвечаю вежливо и формально, предоставляю точную информацию и помогаю с различными задачами. Соблюдаю этические принципы и не использую неформальную лексику."""
        self.system_prompt_edit.setPlainText(template)
    
    def load_friend_template(self):
        """Загрузка шаблона подруги"""
        template = """Привет! Я Сакура, твоя виртуальная подруга! Люблю общаться, делиться мыслями и эмоциями. Интересуюсь твоими делами, поддерживаю в трудную минуту и радуюсь твоим успехам. Говорю дружелюбно и тепло."""
        self.system_prompt_edit.setPlainText(template)
    
    def load_settings(self):
        """Загрузка настроек"""
        self.name_edit.setText(config.get('personality.name', 'Сакура'))
        self.system_prompt_edit.setPlainText(config.get('personality.system_prompt', ''))
        self.memory_spin.setValue(config.get('personality.conversation_memory', 50))
    
    def save_settings(self):
        """Сохранение настроек"""
        config.set('personality.name', self.name_edit.text())
        config.set('personality.system_prompt', self.system_prompt_edit.toPlainText())
        config.set('personality.conversation_memory', self.memory_spin.value())


class ModulesTab(QScrollArea):
    """Вкладка настройки модулей"""
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        content_widget = QWidget()
        self.setWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        
        # Группа "Синтез речи (TTS)"
        tts_group = QGroupBox("Синтез речи (Silero TTS)")
        tts_layout = QFormLayout(tts_group)
        
        # Включение TTS
        self.tts_enabled_check = QCheckBox("Включить синтез речи")
        tts_layout.addRow(self.tts_enabled_check)
        
        # Модель TTS
        self.tts_model_combo = QComboBox()
        self.tts_model_combo.addItems(["v4_ru", "v3_ru"])
        tts_layout.addRow("Модель:", self.tts_model_combo)
        
        # Спикер
        self.tts_speaker_combo = QComboBox()
        self.tts_speaker_combo.addItems(["baya", "aidar", "kseniya", "xenia", "eugene"])
        tts_layout.addRow("Голос:", self.tts_speaker_combo)
        
        # Частота дискретизации
        self.tts_sample_rate_combo = QComboBox()
        self.tts_sample_rate_combo.addItems(["48000", "24000", "8000"])
        tts_layout.addRow("Частота дискретизации:", self.tts_sample_rate_combo)
        
        # Устройство
        self.tts_device_combo = QComboBox()
        self.tts_device_combo.addItems(["cpu", "cuda"])
        tts_layout.addRow("Устройство:", self.tts_device_combo)
        
        # Громкость
        volume_layout = QHBoxLayout()
        self.tts_volume_slider = QSlider(Qt.Horizontal)
        self.tts_volume_slider.setRange(0, 100)
        self.tts_volume_label = QLabel("80%")
        self.tts_volume_slider.valueChanged.connect(
            lambda v: self.tts_volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.tts_volume_slider)
        volume_layout.addWidget(self.tts_volume_label)
        tts_layout.addRow("Громкость:", volume_layout)
        
        # Тест TTS
        self.tts_test_btn = QPushButton("Тест голоса")
        self.tts_test_btn.clicked.connect(self.test_tts)
        tts_layout.addRow(self.tts_test_btn)
        
        layout.addWidget(tts_group)
        
        # Группа "Распознавание речи (STT)"
        stt_group = QGroupBox("Распознавание речи (Vosk)")
        stt_layout = QFormLayout(stt_group)
        
        # Включение STT
        self.stt_enabled_check = QCheckBox("Включить распознавание речи")
        stt_layout.addRow(self.stt_enabled_check)
        
        # Путь к модели
        model_layout = QHBoxLayout()
        self.stt_model_edit = QLineEdit()
        self.stt_model_btn = QPushButton("Выбрать")
        self.stt_model_btn.clicked.connect(self.choose_stt_model)
        model_layout.addWidget(self.stt_model_edit)
        model_layout.addWidget(self.stt_model_btn)
        stt_layout.addRow("Путь к модели:", model_layout)
        
        # Автозагрузка модели
        self.stt_auto_download_check = QCheckBox("Автоматически скачивать модель")
        stt_layout.addRow(self.stt_auto_download_check)
        
        # Частота дискретизации
        self.stt_sample_rate_spin = QSpinBox()
        self.stt_sample_rate_spin.setRange(8000, 48000)
        self.stt_sample_rate_spin.setSingleStep(8000)
        stt_layout.addRow("Частота дискретизации:", self.stt_sample_rate_spin)
        
        # Размер буфера
        self.stt_chunk_size_spin = QSpinBox()
        self.stt_chunk_size_spin.setRange(1024, 8192)
        self.stt_chunk_size_spin.setSingleStep(1024)
        stt_layout.addRow("Размер буфера:", self.stt_chunk_size_spin)
        
        # Тест микрофона
        self.stt_test_btn = QPushButton("Тест микрофона")
        self.stt_test_btn.clicked.connect(self.test_microphone)
        stt_layout.addRow(self.stt_test_btn)
        
        layout.addWidget(stt_group)
        
        # Группа "Аудио"
        audio_group = QGroupBox("Аудио устройства")
        audio_layout = QFormLayout(audio_group)
        
        # Устройство ввода
        self.audio_input_combo = QComboBox()
        self.audio_input_combo.addItem("По умолчанию", None)
        audio_layout.addRow("Микрофон:", self.audio_input_combo)
        
        # Устройство вывода
        self.audio_output_combo = QComboBox()
        self.audio_output_combo.addItem("По умолчанию", None)
        audio_layout.addRow("Динамики:", self.audio_output_combo)
        
        # Порог активности голоса
        vad_layout = QHBoxLayout()
        self.vad_threshold_slider = QSlider(Qt.Horizontal)
        self.vad_threshold_slider.setRange(0, 100)
        self.vad_threshold_label = QLabel("30%")
        self.vad_threshold_slider.valueChanged.connect(
            lambda v: self.vad_threshold_label.setText(f"{v}%")
        )
        vad_layout.addWidget(self.vad_threshold_slider)
        vad_layout.addWidget(self.vad_threshold_label)
        audio_layout.addRow("Порог активности:", vad_layout)
        
        # Таймаут тишины
        self.silence_timeout_spin = QDoubleSpinBox()
        self.silence_timeout_spin.setRange(0.5, 10.0)
        self.silence_timeout_spin.setSingleStep(0.5)
        self.silence_timeout_spin.setSuffix(" сек")
        audio_layout.addRow("Таймаут тишины:", self.silence_timeout_spin)
        
        layout.addWidget(audio_group)
        layout.addStretch()
    
    def choose_stt_model(self):
        """Выбор модели STT"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку с моделью Vosk",
            "models/"
        )
        if folder_path:
            self.stt_model_edit.setText(folder_path)
    
    def test_tts(self):
        """Тест синтеза речи"""
        from tts.silero_tts import SileroTTS
        
        try:
            tts = SileroTTS()
            tts.test_speech()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка тестирования TTS:\n{e}")
    
    def test_microphone(self):
        """Тест микрофона"""
        from stt.vosk_stt import VoskSTT
        
        try:
            stt = VoskSTT()
            if stt.test_microphone():
                QMessageBox.information(self, "Успех", "Микрофон работает правильно")
            else:
                QMessageBox.warning(self, "Ошибка", "Проблема с микрофоном")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка тестирования микрофона:\n{e}")
    
    def load_settings(self):
        """Загрузка настроек"""
        # TTS
        self.tts_enabled_check.setChecked(config.get('tts.enabled', True))
        self.tts_model_combo.setCurrentText(config.get('tts.model', 'v4_ru'))
        self.tts_speaker_combo.setCurrentText(config.get('tts.speaker', 'baya'))
        self.tts_sample_rate_combo.setCurrentText(str(config.get('tts.sample_rate', 48000)))
        self.tts_device_combo.setCurrentText(config.get('tts.device', 'cpu'))
        self.tts_volume_slider.setValue(int(config.get('tts.volume', 0.8) * 100))
        
        # STT
        self.stt_enabled_check.setChecked(config.get('stt.enabled', True))
        self.stt_model_edit.setText(config.get('stt.model_path', 'models/vosk-model-ru-0.42'))
        self.stt_auto_download_check.setChecked(config.get('stt.auto_download', True))
        self.stt_sample_rate_spin.setValue(config.get('stt.sample_rate', 16000))
        self.stt_chunk_size_spin.setValue(config.get('stt.chunk_size', 4096))
        
        # Audio
        self.vad_threshold_slider.setValue(int(config.get('audio.vad_threshold', 0.3) * 100))
        self.silence_timeout_spin.setValue(config.get('audio.silence_timeout', 2.0))
    
    def save_settings(self):
        """Сохранение настроек"""
        # TTS
        config.set('tts.enabled', self.tts_enabled_check.isChecked())
        config.set('tts.model', self.tts_model_combo.currentText())
        config.set('tts.speaker', self.tts_speaker_combo.currentText())
        config.set('tts.sample_rate', int(self.tts_sample_rate_combo.currentText()))
        config.set('tts.device', self.tts_device_combo.currentText())
        config.set('tts.volume', self.tts_volume_slider.value() / 100)
        
        # STT
        config.set('stt.enabled', self.stt_enabled_check.isChecked())
        config.set('stt.model_path', self.stt_model_edit.text())
        config.set('stt.auto_download', self.stt_auto_download_check.isChecked())
        config.set('stt.sample_rate', self.stt_sample_rate_spin.value())
        config.set('stt.chunk_size', self.stt_chunk_size_spin.value())
        
        # Audio
        config.set('audio.vad_threshold', self.vad_threshold_slider.value() / 100)
        config.set('audio.silence_timeout', self.silence_timeout_spin.value())
