"""
Утилиты для работы с аудио
"""

import numpy as np
import pyaudio
import wave
import threading
import time
from typing import List, Optional, Tuple, Callable
from ..utils.logger import logger


class AudioDeviceManager:
    """Менеджер аудио устройств"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
    
    def get_input_devices(self) -> List[Tuple[int, str]]:
        """Получает список устройств ввода"""
        devices = []
        
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append((i, device_info['name']))
        except Exception as e:
            logger.error(f"Ошибка получения устройств ввода: {e}")
        
        return devices
    
    def get_output_devices(self) -> List[Tuple[int, str]]:
        """Получает список устройств вывода"""
        devices = []
        
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxOutputChannels'] > 0:
                    devices.append((i, device_info['name']))
        except Exception as e:
            logger.error(f"Ошибка получения устройств вывода: {e}")
        
        return devices
    
    def get_default_input_device(self) -> Optional[int]:
        """Получает устройство ввода по умолчанию"""
        try:
            device_info = self.audio.get_default_input_device_info()
            return device_info['index']
        except Exception as e:
            logger.error(f"Ошибка получения устройства ввода по умолчанию: {e}")
            return None
    
    def get_default_output_device(self) -> Optional[int]:
        """Получает устройство вывода по умолчанию"""
        try:
            device_info = self.audio.get_default_output_device_info()
            return device_info['index']
        except Exception as e:
            logger.error(f"Ошибка получения устройства вывода по умолчанию: {e}")
            return None
    
    def test_device(self, device_id: int, is_input: bool = True) -> bool:
        """Тестирует аудио устройство"""
        try:
            if is_input:
                # Тест устройства ввода
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=device_id,
                    frames_per_buffer=1024
                )
                
                # Читаем небольшой фрагмент
                data = stream.read(1024, exception_on_overflow=False)
                stream.stop_stream()
                stream.close()
                
                return len(data) > 0
            else:
                # Тест устройства вывода
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    output=True,
                    output_device_index=device_id,
                    frames_per_buffer=1024
                )
                
                # Воспроизводим тишину
                silence = b'\x00\x00' * 1024
                stream.write(silence)
                stream.stop_stream()
                stream.close()
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка тестирования устройства {device_id}: {e}")
            return False
    
    def __del__(self):
        """Деструктор"""
        try:
            self.audio.terminate()
        except:
            pass


class VoiceActivityDetector:
    """Детектор голосовой активности"""
    
    def __init__(self, threshold: float = 0.02, window_size: int = 1024):
        self.threshold = threshold
        self.window_size = window_size
        self.noise_level = 0.0
        self.calibrated = False
    
    def calibrate(self, audio_data: np.ndarray, duration: float = 2.0) -> None:
        """Калибровка по уровню шума"""
        try:
            # Вычисляем RMS для калибровки
            rms = np.sqrt(np.mean(audio_data ** 2))
            self.noise_level = rms * 1.5  # Немного выше уровня шума
            self.calibrated = True
            
            logger.info(f"VAD откалиброван: уровень шума = {self.noise_level:.6f}")
            
        except Exception as e:
            logger.error(f"Ошибка калибровки VAD: {e}")
    
    def is_speech(self, audio_data: np.ndarray) -> bool:
        """Определяет наличие речи в аудио данных"""
        try:
            # Конвертируем в float если нужно
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Вычисляем RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            # Используем калиброванный или фиксированный порог
            if self.calibrated:
                return rms > self.noise_level
            else:
                return rms > self.threshold
                
        except Exception as e:
            logger.error(f"Ошибка детекции голоса: {e}")
            return False
    
    def set_threshold(self, threshold: float) -> None:
        """Устанавливает порог детекции"""
        self.threshold = threshold
        logger.info(f"Порог VAD установлен: {threshold}")


class AudioRecorder:
    """Записывает аудио в отдельном потоке"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 device_id: Optional[int] = None):
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_id = device_id
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.recording = False
        self.frames: List[bytes] = []
        
        # Callbacks
        self.on_data: Optional[Callable[[np.ndarray], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
    
    def start_recording(self) -> bool:
        """Начинает запись"""
        if self.recording:
            return True
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_id,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.recording = True
            self.frames.clear()
            self.stream.start_stream()
            
            if self.on_start:
                self.on_start()
            
            logger.info("Запись аудио начата")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка начала записи: {e}")
            return False
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """Останавливает запись и возвращает данные"""
        if not self.recording:
            return None
        
        try:
            self.recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            if self.on_stop:
                self.on_stop()
            
            # Объединяем записанные данные
            if self.frames:
                audio_data = b''.join(self.frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                logger.info(f"Запись остановлена. Записано {len(audio_array)} семплов")
                return audio_array
            
        except Exception as e:
            logger.error(f"Ошибка остановки записи: {e}")
        
        return None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для получения аудио данных"""
        if self.recording:
            self.frames.append(in_data)
            
            # Вызываем callback с данными
            if self.on_data:
                try:
                    audio_array = np.frombuffer(in_data, dtype=np.int16)
                    self.on_data(audio_array)
                except Exception as e:
                    logger.error(f"Ошибка в audio callback: {e}")
        
        return (None, pyaudio.paContinue)
    
    def save_to_file(self, filename: str, audio_data: np.ndarray) -> bool:
        """Сохраняет аудио в WAV файл"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            logger.info(f"Аудио сохранено в файл: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения аудио: {e}")
            return False
    
    def __del__(self):
        """Деструктор"""
        self.stop_recording()
        try:
            self.audio.terminate()
        except:
            pass


class AudioProcessor:
    """Процессор аудио с различными эффектами"""
    
    @staticmethod
    def normalize_audio(audio: np.ndarray, target_level: float = 0.8) -> np.ndarray:
        """Нормализует громкость аудио"""
        try:
            # Находим максимальное значение
            max_val = np.max(np.abs(audio))
            
            if max_val > 0:
                # Нормализуем к целевому уровню
                normalized = audio * (target_level / max_val)
                return normalized.astype(audio.dtype)
            
            return audio
            
        except Exception as e:
            logger.error(f"Ошибка нормализации аудио: {e}")
            return audio
    
    @staticmethod
    def apply_gain(audio: np.ndarray, gain_db: float) -> np.ndarray:
        """Применяет усиление в дБ"""
        try:
            # Конвертируем дБ в линейный коэффициент
            gain_linear = 10 ** (gain_db / 20)
            
            # Применяем усиление
            amplified = audio * gain_linear
            
            # Ограничиваем диапазон
            if audio.dtype == np.int16:
                amplified = np.clip(amplified, -32768, 32767)
            elif audio.dtype == np.float32:
                amplified = np.clip(amplified, -1.0, 1.0)
            
            return amplified.astype(audio.dtype)
            
        except Exception as e:
            logger.error(f"Ошибка применения усиления: {e}")
            return audio
    
    @staticmethod
    def remove_silence(audio: np.ndarray, 
                      threshold: float = 0.01, 
                      min_silence_duration: float = 0.5,
                      sample_rate: int = 16000) -> np.ndarray:
        """Удаляет тишину из аудио"""
        try:
            # Размер окна для анализа тишины
            window_size = int(min_silence_duration * sample_rate)
            
            # Конвертируем в float для анализа
            if audio.dtype == np.int16:
                audio_float = audio.astype(np.float32) / 32768.0
            else:
                audio_float = audio.astype(np.float32)
            
            # Находим участки с речью
            speech_mask = np.zeros(len(audio_float), dtype=bool)
            
            for i in range(0, len(audio_float) - window_size, window_size // 4):
                window = audio_float[i:i + window_size]
                rms = np.sqrt(np.mean(window ** 2))
                
                if rms > threshold:
                    speech_mask[i:i + window_size] = True
            
            # Оставляем только участки с речью
            speech_audio = audio[speech_mask]
            
            logger.info(f"Удалена тишина: {len(audio)} -> {len(speech_audio)} семплов")
            return speech_audio
            
        except Exception as e:
            logger.error(f"Ошибка удаления тишины: {e}")
            return audio


# Глобальные экземпляры
device_manager = AudioDeviceManager()
