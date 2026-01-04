# Инструкция по интеграции

## Обзор архитектуры

AI-модуль состоит из следующих компонентов:

1. **Telegram Bot** (`bot.py`) - обработка сообщений от пользователей
2. **LLM Service** (`llm_service.py`) - взаимодействие с OpenAI API
3. **Storage** (`storage.py`) - хранение диалогов (в памяти для MVP)
4. **Prompts** (`prompts.py`) - системный промпт для AI

## Логика работы

### Поток данных

```
Пользователь → Telegram Bot → LLM Service → OpenAI API
                ↓
            Storage (сохранение истории)
                ↓
            Формирование саммари
                ↓
            Логирование/Передача в CRM
```

### Процесс квалификации

1. Пользователь отправляет `/start` - создаётся новый диалог
2. Каждое сообщение пользователя добавляется в историю диалога
3. История отправляется в LLM с системным промптом
4. LLM генерирует ответ и проверяет, завершён ли диалог
5. Если диалог завершён, извлекается саммари
6. Саммари сохраняется в storage

### Формат саммари

Саммари представляет собой словарь Python:
```python
{
    "Запрос клиента": "текст запроса",
    "Сроки": "есть до 12 мес / 24+ мес / нет / не определены",
    "Масштаб": "малый / средний / крупный / неизвестен",
    "КЭВ": "да / нет / не определено",
    "Следующий шаг": "рекомендация",
    "Категория": "A / B / C"
}
```

## Интеграция с базой данных

### Вариант 1: SQLite

```python
# storage_db.py
import sqlite3
from datetime import datetime
import json

class DialogStorageDB:
    def __init__(self, db_path="dialogs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialogs (
                user_id INTEGER PRIMARY KEY,
                messages TEXT,
                is_complete INTEGER,
                summary TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_message(self, user_id: int, role: str, content: str):
        dialog = self.get_dialog(user_id)
        if not dialog:
            messages = []
        else:
            messages = json.loads(dialog['messages'])
        
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO dialogs 
            (user_id, messages, is_complete, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(messages), 0, datetime.now()))
        conn.commit()
        conn.close()
    
    def get_dialog(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM dialogs WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'messages': row[1],
                'is_complete': bool(row[2]),
                'summary': json.loads(row[3]) if row[3] else None
            }
        return None
    
    def mark_complete(self, user_id: int, summary: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE dialogs 
            SET is_complete = 1, summary = ?, updated_at = ?
            WHERE user_id = ?
        ''', (json.dumps(summary), datetime.now(), user_id))
        conn.commit()
        conn.close()
```

### Вариант 2: PostgreSQL

```python
# storage_postgres.py
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

class DialogStoragePostgres:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialogs (
                user_id BIGINT PRIMARY KEY,
                messages JSONB,
                is_complete BOOLEAN DEFAULT FALSE,
                summary JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        self.conn.commit()
        cursor.close()
    
    # Аналогичные методы как в SQLite варианте
```

## Интеграция с CRM

### Webhook для отправки саммари

```python
# crm_integration.py
import requests
import logging

logger = logging.getLogger(__name__)

class CRMIntegration:
    def __init__(self, webhook_url: str, api_key: str = None):
        self.webhook_url = webhook_url
        self.api_key = api_key
    
    def send_summary(self, user_id: int, summary: dict, user_info: dict = None):
        """Отправляет саммари в CRM через webhook"""
        payload = {
            "user_id": user_id,
            "summary": summary,
            "user_info": user_info or {}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Саммари для пользователя {user_id} отправлено в CRM")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки саммари в CRM: {e}")
            return False
```

### Модификация bot.py для интеграции с CRM

```python
# В bot.py добавить:
from crm_integration import CRMIntegration

class QualificationBot:
    def __init__(self):
        # ... существующий код ...
        self.crm = CRMIntegration(
            webhook_url=os.getenv("CRM_WEBHOOK_URL"),
            api_key=os.getenv("CRM_API_KEY")
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # ... существующий код ...
        
        if is_complete and summary:
            self.storage.mark_complete(user_id, summary)
            
            # Отправка в CRM
            user_info = {
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "last_name": update.effective_user.last_name
            }
            self.crm.send_summary(user_id, summary, user_info)
            
            logger.info(f"Диалог завершён для пользователя {user_id}")
```

## REST API для получения саммари

```python
# api.py
from flask import Flask, jsonify, request
from storage import DialogStorage
import os

app = Flask(__name__)
storage = DialogStorage()

@app.route('/api/summary/<int:user_id>', methods=['GET'])
def get_summary(user_id):
    """Получить саммари для пользователя"""
    dialog = storage.get_dialog(user_id)
    
    if not dialog:
        return jsonify({"error": "Dialog not found"}), 404
    
    if not dialog.is_complete:
        return jsonify({"error": "Dialog not completed"}), 400
    
    return jsonify({
        "user_id": user_id,
        "summary": dialog.summary,
        "messages_count": len(dialog.messages)
    })

@app.route('/api/summaries', methods=['GET'])
def get_all_summaries():
    """Получить все завершённые саммари"""
    # Реализация зависит от типа storage
    # Для БД можно сделать запрос
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Настройка системного промпта

Системный промпт находится в `prompts.py`. Для кастомизации:

1. Измените `SYSTEM_PROMPT` в `prompts.py`
2. Добавьте специфичные для вашей компании вопросы
3. Настройте категоризацию под ваши критерии

## Мониторинг и логирование

### Настройка логирования

```python
# В bot.py уже есть базовая настройка
# Для продакшена можно добавить:

import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    handler = RotatingFileHandler(
        'bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
```

## Развёртывание

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
```

## Безопасность

1. **Хранение токенов**: Используйте `.env` файлы, не коммитьте их в репозиторий
2. **Валидация данных**: Добавьте валидацию входящих сообщений
3. **Rate limiting**: Ограничьте количество запросов от одного пользователя
4. **Обработка ошибок**: Всегда обрабатывайте исключения при работе с API

## Тестирование

```python
# test_bot.py
import unittest
from llm_service import LLMService
from storage import DialogStorage
from models import Message
from datetime import datetime

class TestQualificationBot(unittest.TestCase):
    def setUp(self):
        self.llm_service = LLMService()
        self.storage = DialogStorage()
    
    def test_dialog_flow(self):
        user_id = 12345
        dialog = self.storage.create_dialog(user_id)
        
        # Симуляция диалога
        messages = [
            Message("assistant", "Привет! Чем могу помочь?", datetime.now()),
            Message("user", "Нужна автоматизация", datetime.now())
        ]
        
        response, is_complete, summary = self.llm_service.generate_response(messages)
        
        self.assertIsInstance(response, str)
        self.assertIsInstance(is_complete, bool)
```

