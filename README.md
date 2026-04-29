# Product Review Sentiment Analysis MVP

Этот проект — простой, но приближенный к production прототип для сбора отзывов о продуктах, предобработки текста, классификации тональности (sentiment analysis), сохранения результатов в SQLite и визуализации аналитики через веб-дашборд.

---

# Структура проекта

```text
.
├── backend
│   ├── api
│   │   └── routes.py
│   ├── models
│   │   └── review.py
│   ├── schemas
│   │   └── review.py
│   ├── services
│   │   ├── preprocessing.py
│   │   ├── review_service.py
│   │   └── sentiment.py
│   ├── database.py
│   └── main.py
├── data
│   └── sample_reviews.csv
├── frontend
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Архитектура пайплайна

```text
Загрузка CSV
   ↓
FastAPI Backend
   ↓
Предобработка текста
   ↓
Модель анализа тональности
   ↓
SQLite
   ↓
API
   ↓
Frontend Dashboard
```

---

# Возможности

## Загрузка и обработка отзывов

* Загрузка CSV-файлов с отзывами о товарах
* Автоматическая обработка текста отзывов

## Предобработка текста

Включает:

* перевод текста в нижний регистр
* удаление пунктуации
* удаление стоп-слов
* токенизацию

## Анализ тональности

* Классификация отзывов как:

  * Positive (положительные)
  * Negative (отрицательные)
  * Neutral (нейтральные)

* Используется модель Hugging Face:

`cardiffnlp/twitter-roberta-base-sentiment-latest`

* Если модель недоступна или не загружается:

  * автоматически используется облегчённый rule-based анализатор.

## Хранение данных

* SQLite база данных
* ORM через SQLAlchemy
* Сохранение:

  * исходного текста
  * обработанного текста
  * тональности
  * confidence score
  * времени создания записи

## Аналитика и дашборд

* Просмотр всех обработанных отзывов
* Статистика по тональности
* Процент положительных, отрицательных и нейтральных отзывов
* Простая визуализация распределения sentiment

---

# Схема базы данных

## Таблица `reviews`

| Поле           | Тип       | Описание                      |
| -------------- | --------- | ----------------------------- |
| id             | integer   | Первичный ключ                |
| original_text  | text      | Исходный отзыв                |
| processed_text | text      | Текст после очистки           |
| sentiment      | string    | positive / negative / neutral |
| score          | float     | Уверенность модели от 0 до 1  |
| created_at     | timestamp | Время создания                |

---

# Формат CSV

Обязательный столбец:

```csv
review
```

Пример:

```csv
id,review
1,"Great product"
2,"Very bad quality"
```

---

# Запуск локально

## 1. Создать и активировать виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Установить зависимости

```bash
pip install -r requirements.txt
```

## 3. Настроить базу данных

Используется SQLite, отдельный сервер БД не нужен.

Файл базы создаётся автоматически при запуске приложения.

Строка подключения по умолчанию:

```bash
DATABASE_URL=sqlite:///./reviews.db
```

Можно экспортировать вручную:

```bash
export DATABASE_URL="sqlite:///./reviews.db"
```

## 4. Запустить backend и frontend

Frontend раздаётся как статические файлы через FastAPI, поэтому достаточно одной команды:

```bash
uvicorn backend.main:app --reload
```

Открыть в браузере:

Приложение:

```text
http://localhost:8000
```

Swagger API Docs:

```text
http://localhost:8000/docs
```

---

# Запуск через Docker

```bash
docker compose up --build
```

После запуска:

```text
http://localhost:8000
```

Файл SQLite базы (`reviews.db`) будет храниться в корне проекта.

---

# API Endpoints

## Загрузить и обработать CSV

```http
POST /upload
```

## Получить все отзывы

```http
GET /reviews
```

## Получить агрегированную статистику

```http
GET /stats
```

---

# Примечания по модели

Основная модель:

```text
cardiffnlp/twitter-roberta-base-sentiment-latest
```

* При первом запуске Transformers скачает веса модели
* Нужен интернет один раз (если модель не закэширована)
* При недоступности модели приложение продолжает работать благодаря fallback-анализатору

---

# Тестовый датасет

Для быстрой проверки можно использовать:

```text
data/sample_reviews.csv
```

---

# Pipeline Summary

```text
CSV Upload
→ Text Preprocessing
→ Sentiment Classification
→ SQLite Storage
→ REST API
→ Dashboard Analytics
```
