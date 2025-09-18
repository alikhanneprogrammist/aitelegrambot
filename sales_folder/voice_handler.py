import os
import tempfile
import time
from telegram import File
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class VoiceHandler:
    """
    Обработчик голосовых сообщений с использованием OpenAI Audio API
    Использует GPT-4o-mini для распознавания речи
    """
    
    def __init__(self):
        """Инициализация обработчика"""
        self.openai_client = None
        
        # Инициализируем OpenAI клиент
        try:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("✅ OpenAI клиент инициализирован")
            else:
                logger.warning("⚠️ OPENAI_API_KEY не найден в .env файле")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации OpenAI: {e}")
            logger.info("💡 Установите OpenAI: pip install openai")
    
    async def process_voice_message(self, voice_file: File) -> str:
        """
        Обрабатывает голосовое сообщение с помощью Whisper
        
        Args:
            voice_file: Файл голосового сообщения из Telegram
            
        Returns:
            str: Распознанный текст или сообщение об ошибке
        """
        oga_file_path = None
        
        try:
            # Создаем временный файл для голосового сообщения
            # Используем более надежный способ создания временного файла
            temp_dir = tempfile.gettempdir()
            temp_filename = f"voice_{int(time.time())}_{os.getpid()}.oga"
            oga_file_path = os.path.join(temp_dir, temp_filename)
            
            logger.info(f"📁 Создаю временный файл: {oga_file_path}")
            logger.info(f"📁 Директория существует: {os.path.exists(temp_dir)}")
            logger.info(f"📁 Права на запись: {os.access(temp_dir, os.W_OK)}")
            
            # Скачиваем голосовое сообщение
            logger.info(f"📥 Скачиваю голосовое сообщение в: {oga_file_path}")
            logger.info(f"📁 Абсолютный путь: {os.path.abspath(oga_file_path)}")
            
            # Пробуем скачать файл
            try:
                await voice_file.download_to_drive(oga_file_path)
                logger.info("✅ Файл скачан методом download_to_drive")
            except Exception as download_error:
                logger.warning(f"⚠️ Ошибка download_to_drive: {download_error}")
                # Альтернативный метод скачивания
                try:
                    file_content = await voice_file.download_as_bytearray()
                    with open(oga_file_path, 'wb') as f:
                        f.write(file_content)
                    logger.info("✅ Файл скачан альтернативным методом")
                except Exception as alt_error:
                    logger.error(f"❌ Ошибка альтернативного скачивания: {alt_error}")
                    return f"❌ Не удалось скачать голосовое сообщение: {alt_error}"
            
            # Проверяем, что файл действительно создался
            if not os.path.exists(oga_file_path):
                return "❌ Не удалось скачать голосовое сообщение"
            
            file_size = os.path.getsize(oga_file_path)
            logger.info(f"📁 OGA файл сохранен: {oga_file_path} (размер: {file_size} байт)")
            
            # Проверяем размер файла
            if file_size < 1000:  # Меньше 1KB
                return "❌ Файл слишком маленький, возможно поврежден"
            
            # Распознаем речь с помощью OpenAI Audio API
            if self.openai_client:
                text = self._recognize_speech_openai(oga_file_path)
                if text and len(text.strip()) > 0:
                    logger.info(f"🎤 OpenAI распознавание завершено: {text[:50]}...")
                    return text.strip()
                else:
                    return "❌ Не удалось распознать речь. Попробуйте говорить четче."
            else:
                return "❌ OpenAI клиент не загружен. Проверьте OPENAI_API_KEY в .env файле"
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки голосового сообщения: {e}")
            return f"❌ Ошибка обработки голосового сообщения: {e}"
        finally:
            # Удаляем временный файл
            if oga_file_path and os.path.exists(oga_file_path):
                try:
                    os.unlink(oga_file_path)
                    logger.debug(f"🗑️ Временный файл удален: {oga_file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")
    
    def _recognize_speech_openai(self, audio_file_path: str) -> str:
        """
        Распознает речь с помощью OpenAI Audio API
        
        Args:
            audio_file_path: Путь к аудио файлу (поддерживает OGG, MP3, WAV и др.)
            
        Returns:
            str: Распознанный текст
        """
        try:
            # Проверяем существование файла
            if not os.path.exists(audio_file_path):
                logger.error(f"❌ Файл не найден: {audio_file_path}")
                return ""
            
            # Проверяем размер файла
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                logger.error(f"❌ Файл пустой: {audio_file_path}")
                return ""
            
            # Проверяем права на чтение
            if not os.access(audio_file_path, os.R_OK):
                logger.error(f"❌ Нет прав на чтение файла: {audio_file_path}")
                return ""
            
            logger.info(f"🔄 Начинаю распознавание с OpenAI Audio API... Файл: {audio_file_path} (размер: {file_size} байт)")
            
            # Открываем файл для отправки в OpenAI
            with open(audio_file_path, 'rb') as audio_file:
                # Используем OpenAI Audio API для распознавания речи
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru",  # Русский язык
                    response_format="text"
                )
            
            text = transcript.strip()
            logger.info(f"📊 Результат OpenAI: {len(text)} символов")
            
            return text
            
        except FileNotFoundError as e:
            logger.error(f"❌ Файл не найден для OpenAI: {e}")
            return ""
        except Exception as e:
            logger.error(f"❌ Ошибка распознавания OpenAI: {e}")
            return ""
    
    
    def parse_voice_command(self, recognized_text: str) -> dict:
        """
        Парсит голосовую команду для понимания намерений
        
        Args:
            recognized_text: Распознанный текст
            
        Returns:
            dict: Структурированная информация о команде
        """
        if not self.openai_client:
            return {
                'success': False,
                'error': 'OpenAI AI недоступен для анализа команды'
            }
        
        try:
            # Создаем промпт для анализа голосовой команды
            prompt = f"""
            Проанализируй голосовую команду пользователя и определи, что он хочет сделать.
            
            КОМАНДА: "{recognized_text}"
            
            ПРИОРИТЕТ 1: РАСХОДЫ - если есть слова: потратил, купил, заплатил, оплатил, поел, съел, выпил, заказал (еду/услуги)
            - Определи тип расхода: 
              * personal (личные) - еда, кафе, ресторан, такси, бензин, аренда, продукты, одежда, развлечения
              * office (офисные) - канцелярия, интернет, уборка офиса, аренда офиса, коммунальные услуги офиса
            - Извлеки сумму из текста (числа)
            - Определи категорию: еда, транспорт, жилье, связь, канцелярия, уборка офиса, ресторан, кафе, такси, бензин, аренда и т.д.
            
            ПРИОРИТЕТ 2: ЗАКАЗЫ - если НЕТ упоминания трат, но есть слова: заказ, измени, поменяй, назначь
            1. Изменить количество товара в заказе
            2. Изменить цену в заказе  
            3. Изменить менеджера заказа
            4. Получить информацию о заказе
            5. Обновить зарплату
            6. Другое действие
            
            СТРУКТУРА ОТВЕТА (JSON):
            {{
                "action": "edit_order|get_info|update_salary|add_multiple_expenses|other",
                "order_number": число или null,
                "field_to_change": "quantity|price|manager|null",
                "new_value": "новое значение или null",
                "product_name": "название товара или null",
                "expenses": [
                    {{
                        "expense_type": "personal|office",
                        "amount": число,
                        "category": "категория расхода",
                        "description": "описание расхода"
                    }}
                ],
                "confidence": число от 0 до 1,
                "original_text": "исходный текст"
            }}
            
            ПРИМЕРЫ:
            
            РАСХОДЫ (приоритет 1 - если есть упоминание трат, покупок, оплат):
            
            ОДИНОЧНЫЕ РАСХОДЫ:
            - "потратил 5000 в кафе" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "personal", "amount": 5000, "category": "еда", "description": "кафе"}}]
            - "купил продукты на 15000" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "personal", "amount": 15000, "category": "еда", "description": "продукты"}}]
            - "заплатил за такси 3000" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "personal", "amount": 3000, "category": "транспорт", "description": "такси"}}]
            - "купил канцелярию на 5000" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "office", "amount": 5000, "category": "канцелярия", "description": "канцелярия"}}]
            
            МНОЖЕСТВЕННЫЕ РАСХОДЫ:
            - "поел рамен на 1000 и потратил 150 на автобус" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "personal", "amount": 1000, "category": "еда", "description": "рамен"}}, {{"expense_type": "personal", "amount": 150, "category": "транспорт", "description": "автобус"}}]
            - "купил хлеб за 500 и молоко за 800" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "personal", "amount": 500, "category": "еда", "description": "хлеб"}}, {{"expense_type": "personal", "amount": 800, "category": "еда", "description": "молоко"}}]
            - "заплатил за интернет 25000 и уборку офиса 15000" -> action: "add_multiple_expenses", expenses: [{{"expense_type": "office", "amount": 25000, "category": "связь", "description": "интернет"}}, {{"expense_type": "office", "amount": 15000, "category": "уборка офиса", "description": "уборка офиса"}}]
            
            ЗАКАЗЫ (если НЕТ упоминания трат):
            - "измени количество котлов 3 штуки в номере заказа 2" -> action: "edit_order", order_number: 2, field_to_change: "quantity", new_value: "3", product_name: "котлы"
            - "поменяй цену в заказе 5 на 50000" -> action: "edit_order", order_number: 5, field_to_change: "price", new_value: "50000"
            - "назначь менеджером Алибек в заказе 3" -> action: "edit_order", order_number: 3, field_to_change: "manager", new_value: "Алибек"
            - "измени менеджера на Айдана в заказе 2" -> action: "edit_order", order_number: 2, field_to_change: "manager", new_value: "Айдана"
            - "поменяй менеджера на Тамер в заказе 1" -> action: "edit_order", order_number: 1, field_to_change: "manager", new_value: "Тамер"
            
            ДОСТУПНЫЕ МЕНЕДЖЕРЫ: Алибек, Айдана, Тамер, Диана, Руслан, manager_3, manager_7
            
            ВАЖНО ДЛЯ РАСХОДОВ:
            - ВСЕГДА извлекай сумму из текста (ищи числа: 1000, 2000, 5000, 10000 и т.д.)
            - ВСЕГДА определяй категорию на основе контекста:
              * "поел", "съел", "выпил", "кафе", "ресторан", "еда", "продукты" → "еда"
              * "такси", "бензин", "транспорт" → "транспорт" 
              * "канцелярия", "ручки", "бумага" → "канцелярия"
              * "интернет", "связь" → "связь"
              * "аренда", "жилье" → "жилье"
              * "уборка" → "уборка офиса" (если офис) или "уборка" (если личное)
            - Если сумма не указана явно, попробуй понять из контекста (например, "тысячи" = 1000)
            
            ВАЖНО: 
            - "Айдана" - это полное имя, не сокращай его
            - "Алибек" - это полное имя, не сокращай его
            - "Тамер" - это полное имя, не сокращай его
            - "Диана" - это полное имя, не сокращай его
            - "Руслан" - это полное имя, не сокращай его
            - "обнови зарплату" -> action: "update_salary"
            - "покажи информацию о заказе 1" -> action: "get_info", order_number: 1
            
            ВАЖНО: 
            - Отвечай ТОЛЬКО в формате JSON
            - НЕ добавляй никакого дополнительного текста
            - НЕ используй markdown форматирование
            - Начинай ответ сразу с символа открывающей скобки
            - Заканчивай ответ символом закрывающей скобки
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по анализу голосовых команд. Отвечай ТОЛЬКО в формате JSON без дополнительного текста."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Парсим JSON ответ
            import json
            try:
                response_text = response.choices[0].message.content.strip()
                logger.info(f"📝 Ответ ChatGPT: {response_text[:200]}...")
                
                # Пытаемся найти JSON в ответе
                if '{' in response_text and '}' in response_text:
                    # Ищем JSON блок
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    json_text = response_text[start:end]
                    
                    command_data = json.loads(json_text)
                    command_data['success'] = True
                    logger.info(f"✅ Команда распознана: {command_data.get('action', 'unknown')}")
                    return command_data
                else:
                    logger.warning("⚠️ JSON не найден в ответе ChatGPT")
                    return self._manual_parse_command(recognized_text)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Ошибка парсинга JSON: {e}")
                logger.warning(f"⚠️ Ответ ChatGPT: {response_text}")
                # Если не удалось распарсить JSON, пытаемся извлечь информацию вручную
                return self._manual_parse_command(recognized_text)
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа команды: {e}")
            return {
                'success': False,
                'error': f'Ошибка анализа команды: {e}'
            }
    
    def create_text_command(self, command_data: dict) -> str:
        """
        Создает текстовую команду на основе структурированных данных
        
        Args:
            command_data: Структурированные данные команды
            
        Returns:
            str: Текстовая команда для выполнения
        """
        try:
            action = command_data.get('action', '')
            order_number = command_data.get('order_number')
            field_to_change = command_data.get('field_to_change')
            new_value = command_data.get('new_value')
            product_name = command_data.get('product_name')
            
            if action == 'edit_order' and order_number:
                if field_to_change == 'quantity' and new_value:
                    if product_name:
                        return f"/edit {order_number} {product_name} quantity {new_value}"
                    else:
                        return f"/edit {order_number} quantity {new_value}"
                elif field_to_change == 'price' and new_value:
                    return f"/edit {order_number} price {new_value}"
                elif field_to_change == 'manager' and new_value:
                    return f"/edit {order_number} manager {new_value}"
            
            elif action == 'get_info' and order_number:
                return f"/info {order_number}"
            
            elif action == 'update_salary':
                return "/update"
            
            elif action == 'add_multiple_expenses':
                # Для множественных расходов создаем команды для каждого
                expenses = command_data.get('expenses', [])
                commands = []
                for expense in expenses:
                    expense_type = expense.get('expense_type', 'personal')
                    amount = expense.get('amount', 0)
                    category = expense.get('category', 'другое')
                    description = expense.get('description', '')
                    
                    if expense_type == 'personal':
                        commands.append(f"потратил {amount} на {category} ({description})")
                    else:  # office
                        commands.append(f"купил {description} на {amount} ({category})")
                
                return " | ".join(commands)
            
            else:
                # Возвращаем исходный текст как команду
                return command_data.get('original_text', '')
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания текстовой команды: {e}")
            return command_data.get('original_text', '')
    
    

# Пример использования
if __name__ == "__main__":
    handler = VoiceHandler()
    info = handler.get_model_info()
    print("🎤 Voice Handler готов к работе!")
    print(f"📊 Статус моделей: {info}")