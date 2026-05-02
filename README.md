# Product Review Sentiment Analysis MVP

Веб-приложение для анализа отзывов о товарах. Проект собирает отзывы из CSV-файлов или API маркетплейсов, очищает текст, определяет общую тональность, находит причины негатива по аспектам и показывает аналитику в dashboard.

Проект сделан как MVP: архитектура простая, но приближенная к реальному backend/frontend приложению на FastAPI, SQLAlchemy и vanilla JavaScript.

## Основной pipeline

```text
CSV / Marketplace API
  -> preprocessing
  -> general sentiment
  -> aspect sentiment
  -> problem extraction
  -> business insights
  -> SQLite
  -> dashboard
```

## Возможности

- Загрузка отзывов из CSV-файла.
- Сбор отзывов из поддерживаемых маркетплейсов.
- Предобработка текста: нижний регистр, удаление пунктуации, токенизация, фильтрация стоп-слов.
- Общий sentiment analysis: `positive`, `negative`, `neutral`.
- Aspect-based sentiment analysis по аспектам:
  - `quality`
  - `delivery`
  - `packaging`
  - `price`
  - `usability`
  - `support`
- Подсчет главных негативных проблем.
- Генерация rule-based business insights и рекомендаций.
- Хранение отзывов и результатов анализа в SQLite.
- Удаление отзывов из истории с пересчетом аналитики.
- Dashboard со статистикой, распределением тональности, проблемами, инсайтами и таблицей обработанных отзывов.

## Структура проекта

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
│   │   ├── aspect_analysis.py
│   │   ├── insights.py
│   │   ├── preprocessing.py
│   │   ├── review_service.py
│   │   ├── sentiment.py
│   │   └── marketplaces
│   │       ├── base.py
│   │       ├── ozon.py
│   │       ├── wildberries.py
│   │       └── yandex_market.py
│   ├── database.py
│   └── main.py
├── data
│   └── sample_reviews.csv
├── frontend
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Backend

Backend написан на FastAPI.

Основные части:

- `backend/main.py` - создание приложения, CORS, подключение роутов и раздача frontend.
- `backend/api/routes.py` - HTTP endpoints.
- `backend/database.py` - подключение к SQLite и авто-добавление недостающих колонок.
- `backend/models/review.py` - SQLAlchemy модель отзыва.
- `backend/schemas/review.py` - Pydantic-схемы API.
- `backend/services/review_service.py` - сохранение, удаление, статистика и top problems.
- `backend/services/sentiment.py` - общий анализ тональности.
- `backend/services/aspect_analysis.py` - rule-based аспектный анализ.
- `backend/services/insights.py` - rule-based бизнес-инсайты.

## Frontend

Frontend сделан на HTML, CSS и JavaScript без отдельного фреймворка.

Dashboard умеет:

- загружать CSV;
- запускать сбор из маркетплейса;
- показывать проценты позитивных, негативных и нейтральных отзывов;
- показывать распределение тональности;
- показывать главные негативные проблемы;
- показывать summary, уровень риска и рекомендации;
- отображать обработанные отзывы;
- удалять отзывы из базы и аналитики.

## Анализ тональности

Основная модель задается в `backend/services/sentiment.py`:

```text
cointegrated/rubert-tiny-sentiment-balanced
```

Если модель недоступна, используется fallback-анализатор на правилах. Он учитывает русские позитивные и негативные слова, отрицания, усилители и восклицательные знаки.

## Aspect-based sentiment analysis

Для MVP используется rule-based подход на русском языке. Каждый аспект получает результат:

```json
{
  "quality": {"sentiment": "positive", "score": 1.0},
  "delivery": {"sentiment": "neutral", "score": 0.0},
  "packaging": {"sentiment": "negative", "score": 1.0}
}
```

Если аспект в отзыве не найден, он получает:

```json
{"sentiment": "neutral", "score": 0.0}
```

## Business insights

Инсайты строятся на основе общей статистики и top problems.

Уровень риска:

- `high` - если доля негативных отзывов больше 40%;
- `medium` - если доля негативных отзывов от 20% до 40%;
- `low` - если доля негативных отзывов меньше 20%.

Рекомендации зависят от проблемного аспекта: упаковка, доставка, качество, цена, удобство или поддержка.

## База данных

Используется SQLite. По умолчанию файл базы хранится в корне проекта:

```text
reviews.db
```

Таблица: `reviews`

| Поле | Описание |
| --- | --- |
| `id` | Внутренний ID отзыва |
| `product_id` | ID товара |
| `marketplace` | Источник отзыва |
| `external_review_id` | ID отзыва во внешней системе |
| `original_text` | Исходный текст |
| `processed_text` | Текст после предобработки |
| `rating` | Оценка товара |
| `review_date` | Дата отзыва |
| `author` | Автор |
| `source_url` | Ссылка на источник |
| `sentiment` | Общая тональность |
| `score` | Уверенность модели |
| `aspects` | JSON с аспектным анализом |
| `created_at` | Дата добавления в базу |

При старте приложения выполняется простая auto-migration проверка, которая добавляет недостающие колонки в существующую таблицу.

## Формат CSV

Обязательная колонка:

```text
review
```

Дополнительные поддерживаемые колонки:

```text
id
external_review_id
product_id
marketplace
rating
review_date
author
source_url
```

Пример:

```csv
id,review,product_id,marketplace,rating
1,"Упаковка повреждена, коробка мятая",sku-100,csv,2
2,"Товар качественный, пользоваться удобно",sku-100,csv,5
```

Тестовый файл:

```text
data/sample_reviews.csv
```

## API

### Загрузка CSV

```http
POST /upload
```

Принимает CSV-файл, анализирует отзывы и сохраняет их в базу.

### Сбор из маркетплейса

```http
POST /collect
```

Пример тела запроса:

```json
{
  "marketplace": "wildberries",
  "product_id": "123456",
  "date_from": "2026-01-01",
  "date_to": "2026-01-31"
}
```

Поддерживаемые значения `marketplace`:

- `wildberries`
- `yandex_market`
- `ozon`

Важно: Ozon в текущем MVP является заглушкой и возвращает `501`, пока не подключен подтвержденный API-метод.

### Получить отзывы

```http
GET /reviews
```

### Удалить отзыв

```http
DELETE /reviews/{review_id}
```

Удаляет запись физически из SQLite. После удаления отзыв не участвует в `/reviews`, `/stats`, `/problems` и `/insights`.

Успешный ответ:

```json
{
  "message": "Review deleted successfully"
}
```

### Статистика тональности

```http
GET /stats
```

Пример ответа:

```json
{
  "total_reviews": 10,
  "positive_percentage": 40.0,
  "negative_percentage": 30.0,
  "neutral_percentage": 30.0
}
```

### Главные проблемы

```http
GET /problems
```

Пример ответа:

```json
{
  "total_negative_aspect_mentions": 6,
  "problems": [
    {
      "aspect": "packaging",
      "count": 2,
      "percentage": 33.33
    }
  ]
}
```

### Инсайты

```http
GET /insights
```

Пример ответа:

```json
{
  "summary": "Основная проблема товара связана с упаковкой...",
  "risk_level": "medium",
  "recommendations": [
    "Проверить упаковку товара и качество защиты при доставке"
  ]
}
```

## Переменные окружения

Базовая переменная:

```env
DATABASE_URL=sqlite:///./reviews.db
```

Для Wildberries:

```env
WB_API_TOKEN=...
```

Для Yandex Market:

```env
YANDEX_MARKET_BUSINESS_ID=...
YANDEX_MARKET_API_KEY=...
```

## Локальный запуск

Создать и активировать виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

Запустить приложение:

```bash
uvicorn backend.main:app --reload
```

Открыть:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Запуск через Docker

```bash
docker compose up --build
```

После запуска открыть:

```text
http://localhost:8000
```

Если нужно применить изменения после правок кода:

```bash
docker compose down
docker compose up --build
```

## Быстрые curl-примеры

```bash
curl http://localhost:8000/reviews
curl http://localhost:8000/stats
curl http://localhost:8000/problems
curl http://localhost:8000/insights
curl -X DELETE http://localhost:8000/reviews/1
```

## Ограничения MVP

- Aspect analysis и insights сделаны rule-based, без отдельной LLM.
- SQLite подходит для прототипа, но для production лучше использовать PostgreSQL.
- Ozon-клиент пока не подключен к реальному API.
- Первый запуск ML-модели может потребовать интернет для загрузки весов.
- CSV читается как UTF-8.
- Дедупликация внешних отзывов работает по паре `marketplace + external_review_id`; CSV-записи могут загружаться повторно.
