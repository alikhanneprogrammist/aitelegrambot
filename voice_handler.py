import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from telegram import File
import google.generativeai as genai
from dotenv import load_dotenv

# Настройка ffmpeg для pydub

try:
    import imageio_ffmpeg as ffmpeg
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    
    # Устанавливаем переменные среды для текущего процесса
    os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path
    
    # Настраиваем pydub
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    
    # Для ffprobe пытаемся найти в той же директории
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe.exe')
    
    if not os.path.exists(ffprobe_path):
        # Пытаемся найти ffprobe с другим именем
        ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe')
    
    if os.path.exists(ffprobe_path):
        AudioSegment.ffprobe = ffprobe_path
        print(f"🔧 Настроен ffmpeg: {ffmpeg_path}")
        print(f"🔧 Настроен ffprobe: {ffprobe_path}")
    else:
        print(f"🔧 Настроен ffmpeg: {ffmpeg_path}")
        print("⚠️ ffprobe не найден, используем только ffmpeg")
        
    # Добавляем директорию с ffmpeg в PATH для текущего процесса
    current_path = os.environ.get('PATH', '')
    if ffmpeg_dir not in current_path:
        os.environ['PATH'] = f"{ffmpeg_dir};{current_path}"
        print(f"🔧 Добавлен в PATH: {ffmpeg_dir}")
        
except ImportError:
    print("⚠️ imageio-ffmpeg недоступен, pydub попытается найти ffmpeg в PATH")
except Exception as e:
    print(f"⚠️ Ошибка настройки ffmpeg: {e}")

load_dotenv()

class VoiceHandler:
    def __init__(self):
        """Инициализация обработчика голосовых сообщений"""
        self.recognizer = sr.Recognizer()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def process_voice_message(self, voice_file: File):
        """
        Обрабатывает голосовое сообщение и преобразует его в текст
        
        Args:
            voice_file (File): Голосовой файл от Telegram
            
        Returns:
            str: Распознанный текст или сообщение об ошибке
        """
        oga_file_path = None
        wav_file_path = None
        
        try:
            # Создаем временный файл для голосового сообщения
            with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as temp_oga:
                oga_file_path = temp_oga.name
                # Скачиваем голосовое сообщение
                await voice_file.download_to_drive(oga_file_path)
                
            # Пытаемся разные способы обработки аудио
            try:
                # Способ 1: Конвертация через pydub (требует ffmpeg)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    wav_file_path = temp_wav.name
                    
                try:
                    print(f"🔄 Конвертирую OGA в WAV через ffmpeg...")
                    print(f"📁 OGA файл: {oga_file_path} (размер: {os.path.getsize(oga_file_path)} байт)")
                    
                    # Способ 1: Прямая конвертация через subprocess (самый надежный)
                    success = self._convert_oga_to_wav_direct(oga_file_path, wav_file_path)
                    
                    if success:
                        print(f"✅ Конвертация завершена (размер: {os.path.getsize(wav_file_path)} байт)")
                        
                        # Распознаем речь
                        text = self._recognize_speech(wav_file_path)
                        print(f"🎤 Распознавание завершено: {text[:50]}...")
                        
                        return text
                    else:
                        # Если прямая конвертация не удалась, пробуем pydub
                        print("⚠️ Прямая конвертация не удалась, пробую через pydub...")
                        
                        try:
                            # Загружаем OGA файл через pydub
                            audio = AudioSegment.from_ogg(oga_file_path)
                            print(f"✅ OGA загружен через pydub (длительность: {len(audio)}ms)")
                            
                            # Экспортируем в WAV
                            audio.export(wav_file_path, format="wav")
                            print(f"✅ Конвертация через pydub завершена")
                            
                            # Распознаем речь
                            text = self._recognize_speech(wav_file_path)
                            print(f"🎤 Распознавание завершено: {text[:50]}...")
                            
                            return text
                            
                        except Exception as pydub_error:
                            print(f"❌ Ошибка pydub: {type(pydub_error).__name__}: {str(pydub_error)}")
                            raise pydub_error
                    
                except Exception as conv_error:
                    print(f"❌ Все способы конвертации не удались: {type(conv_error).__name__}: {str(conv_error)}")
                    
                    # Способ 2: Попытка прямого распознавания OGA (почти всегда не работает)
                    try:
                        text = self._recognize_speech_from_oga(oga_file_path)
                        return text
                    except Exception as oga_error:
                        print(f"⚠️ Ошибка распознавания OGA: {oga_error}")
                        
                        # Способ 3: Возвращаем подробное сообщение с инструкциями
                        return ("❌ Не удалось обработать голосовое сообщение.\n\n"
                               f"🔍 **Детали ошибки:** {str(conv_error)}\n\n"
                               "🔧 **Решение:** FFmpeg настроен, но возникла ошибка конвертации.\n\n"
                               "💡 **Альтернативы:**\n"
                               "• Отправьте текстовое сообщение с тем же запросом\n"
                               "• Используйте команды: /edit, /analyze, /ask")
                        
            except Exception as e:
                return f"❌ Общая ошибка обработки голосового сообщения: {str(e)}"
                
        except Exception as e:
            return f"Ошибка при обработке голосового сообщения: {str(e)}"
        
        finally:
            # Безопасно удаляем временные файлы в любом случае
            if oga_file_path:
                self._safe_delete_file(oga_file_path)
            if wav_file_path:
                self._safe_delete_file(wav_file_path)
    
    def _recognize_speech(self, wav_file_path):
        """
        Распознает речь из WAV файла
        
        Args:
            wav_file_path (str): Путь к WAV файлу
            
        Returns:
            str: Распознанный текст
        """
        try:
            with sr.AudioFile(wav_file_path) as source:
                # Записываем аудио из файла
                audio = self.recognizer.record(source)
                
                # Пробуем разные методы распознавания
                try:
                    # Пробуем Google Speech Recognition (бесплатный)
                    text = self.recognizer.recognize_google(audio, language='ru-RU')
                    return text
                except sr.UnknownValueError:
                    # Если Google не смог распознать, пробуем Sphinx (офлайн)
                    try:
                        text = self.recognizer.recognize_sphinx(audio, language='ru-RU')
                        return text
                    except:
                        return "❌ Не удалось распознать речь. Попробуйте говорить четче."
                except sr.RequestError as e:
                    return f"❌ Ошибка сервиса распознавания: {e}"
                    
        except Exception as e:
            return f"❌ Ошибка при чтении аудио файла: {e}"
    
    def _recognize_speech_from_oga(self, oga_file_path):
        """
        Пытается распознать речь напрямую из OGA файла (без конвертации)
        Это почти всегда не работает, так как SpeechRecognition не поддерживает OGA
        
        Args:
            oga_file_path (str): Путь к OGA файлу
            
        Returns:
            str: Распознанный текст или сообщение об ошибке
        """
        # OGA файлы не поддерживаются SpeechRecognition напрямую
        # Возвращаем информативное сообщение вместо попытки чтения
        return ("❌ Для обработки голосовых сообщений Telegram (OGA формат) требуется ffmpeg. "
                "Пожалуйста, установите ffmpeg согласно инструкции в файле FFMPEG_INSTALL.md "
                "или отправьте текстовое сообщение.")
    
    def parse_voice_command(self, recognized_text):
        """
        Парсит голосовую команду для понимания намерений
        
        Args:
            recognized_text (str): Распознанный текст
            
        Returns:
            dict: Структурированная информация о команде
        """
        if not self.model:
            return {
                'success': False,
                'error': 'Gemini AI недоступен для анализа команды'
            }
        
        try:
            # Создаем промпт для анализа голосовой команды
            prompt = f"""
            Проанализируй голосовую команду пользователя и определи, что он хочет сделать.
            
            КОМАНДА: "{recognized_text}"
            
            ВОЗМОЖНЫЕ ДЕЙСТВИЯ:
            1. Изменить количество товара в заказе
            2. Изменить цену в заказе  
            3. Изменить менеджера заказа
            4. Получить информацию о заказе
            5. Другое действие
            
            СТРУКТУРА ОТВЕТА (JSON):
            {{
                "action": "edit_order|get_info|other",
                "order_number": число или null,
                "field_to_change": "quantity|price|manager|null",
                "new_value": "новое значение или null",
                "product_name": "название товара или null",
                "confidence": число от 0 до 1,
                "original_text": "исходный текст"
            }}
            
            ПРИМЕРЫ:
            - "измени количество котлов 3 штуки в номере заказа 2" -> action: "edit_order", order_number: 2, field_to_change: "quantity", new_value: "3", product_name: "котлы"
            - "поменяй цену в заказе 5 на 50000" -> action: "edit_order", order_number: 5, field_to_change: "price", new_value: "50000"
            - "назначь менеджером Иван в заказе 3" -> action: "edit_order", order_number: 3, field_to_change: "manager", new_value: "Иван"
            
            ВАЖНО: Отвечай ТОЛЬКО в формате JSON, без дополнительного текста.
            """
            
            response = self.model.generate_content(prompt)
            
            # Парсим JSON ответ
            import json
            try:
                command_data = json.loads(response.text.strip())
                command_data['success'] = True
                return command_data
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, пытаемся извлечь информацию вручную
                return self._manual_parse_command(recognized_text)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка при анализе команды: {str(e)}'
            }
    
    def _manual_parse_command(self, text):
        """
        Ручной парсинг команды как запасной вариант
        
        Args:
            text (str): Текст команды
            
        Returns:
            dict: Информация о команде
        """
        text_lower = text.lower()
        
        # Ищем номер заказа
        order_number = None
        order_keywords = ['заказ', 'заказа', 'заказе', 'номер', 'номера', 'номере']
        for i, word in enumerate(text.split()):
            if any(keyword in word.lower() for keyword in order_keywords):
                # Ищем число рядом
                for j in range(max(0, i-2), min(len(text.split()), i+3)):
                    try:
                        potential_number = text.split()[j].strip('№#.,')
                        if potential_number.isdigit():
                            order_number = int(potential_number)
                            break
                    except:
                        continue
                if order_number:
                    break
        
        # Определяем действие
        action = "other"
        field_to_change = None
        new_value = None
        product_name = None
        
        # Проверяем на изменение количества
        if any(word in text_lower for word in ['количество', 'штук', 'штуки', 'шт']):
            action = "edit_order"
            field_to_change = "quantity"
            
            # Ищем число для количества
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                new_value = numbers[-1]  # Берем последнее число как новое количество
        
        # Проверяем на изменение цены
        elif any(word in text_lower for word in ['цена', 'цену', 'стоимость', 'сумма']):
            action = "edit_order"
            field_to_change = "price"
            
            # Ищем число для цены
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                new_value = numbers[-1]  # Берем последнее число как новую цену
        
        # Проверяем на изменение менеджера
        elif any(word in text_lower for word in ['менеджер', 'менеджера', 'назначь']):
            action = "edit_order"
            field_to_change = "manager"
            
            # Ищем имя (слово с заглавной буквы, не являющееся служебным)
            words = text.split()
            for word in words:
                if word[0].isupper() and word.lower() not in ['заказ', 'заказа', 'заказе', 'менеджер', 'назначь']:
                    new_value = word
                    break
        
        # Ищем название товара
        if any(word in text_lower for word in ['котел', 'котлы', 'котла']):
            product_name = "котлы"
        
        return {
            'success': True,
            'action': action,
            'order_number': order_number,
            'field_to_change': field_to_change,
            'new_value': new_value,
            'product_name': product_name,
            'confidence': 0.7,  # Средняя уверенность для ручного парсинга
            'original_text': text
        }
    
    def create_text_command(self, command_data):
        """
        Создает текстовую команду на основе распознанной голосовой команды
        
        Args:
            command_data (dict): Данные о команде
            
        Returns:
            str: Текстовая команда для существующего обработчика
        """
        if not command_data.get('success'):
            return None
        
        if command_data.get('action') != 'edit_order':
            return command_data.get('original_text', '')
        
        # Формируем команду редактирования
        parts = []
        
        if command_data.get('order_number'):
            parts.append(f"заказ номер {command_data['order_number']}")
        
        if command_data.get('field_to_change') == 'quantity' and command_data.get('new_value'):
            if command_data.get('product_name'):
                parts.append(f"изменить количество {command_data['product_name']} на {command_data['new_value']}")
            else:
                parts.append(f"изменить количество на {command_data['new_value']}")
        
        elif command_data.get('field_to_change') == 'price' and command_data.get('new_value'):
            parts.append(f"изменить цену на {command_data['new_value']}")
        
        elif command_data.get('field_to_change') == 'manager' and command_data.get('new_value'):
            parts.append(f"назначить менеджером {command_data['new_value']}")
        
        if parts:
            return " ".join(parts)
        else:
            # Если не удалось сформировать структурированную команду, возвращаем оригинальный текст
            return command_data.get('original_text', '')
    
    def _safe_delete_file(self, file_path):
        """
        Безопасно удаляет файл, игнорируя ошибки доступа
        
        Args:
            file_path (str): Путь к файлу для удаления
        """
        import time
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    return True
            except PermissionError:
                # Файл может быть заблокирован, ждем немного
                time.sleep(0.1)
                continue
            except Exception as e:
                print(f"⚠️ Не удалось удалить файл {file_path}: {e}")
                break
        
        # Если не удалось удалить, планируем удаление позже
        try:
            import atexit
            atexit.register(lambda: self._cleanup_file(file_path))
        except:
            pass
        
        return False
    
    def _cleanup_file(self, file_path):
        """Отложенная очистка файла при выходе из программы"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass
    
    def _convert_oga_to_wav_direct(self, oga_path, wav_path):
        """
        Прямая конвертация OGA в WAV через subprocess
        
        Args:
            oga_path (str): Путь к входному OGA файлу
            wav_path (str): Путь к выходному WAV файлу
            
        Returns:
            bool: True если конвертация успешна, False иначе
        """
        try:
            import subprocess
            import imageio_ffmpeg as ffmpeg
            
            ffmpeg_exe = ffmpeg.get_ffmpeg_exe()
            
            # Команда для конвертации OGA в WAV
            cmd = [
                ffmpeg_exe,
                "-i", oga_path,           # входной файл
                "-acodec", "pcm_s16le",   # кодек для WAV
                "-ar", "16000",           # частота дискретизации 16kHz (хорошо для распознавания речи)
                "-ac", "1",               # моно
                "-y",                     # перезаписать выходной файл
                wav_path                  # выходной файл
            ]
            
            print(f"🔧 Выполняю команду: {' '.join(cmd[:3])} ... {cmd[-1]}")
            
            # Выполняем команду
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # таймаут 30 секунд
            )
            
            if result.returncode == 0:
                print(f"✅ FFmpeg конвертация успешна")
                return True
            else:
                print(f"❌ FFmpeg ошибка (код {result.returncode}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Таймаут конвертации (>30 сек)")
            return False
        except Exception as e:
            print(f"❌ Ошибка прямой конвертации: {type(e).__name__}: {e}")
            return False
