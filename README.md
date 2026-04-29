# Product Review Sentiment Analysis MVP

This project is a simple but production-like prototype for collecting product reviews, preprocessing text, classifying sentiment, storing results in SQLite, and visualizing analytics in a web dashboard.

## Project Structure

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

## System Pipeline

```text
CSV Upload -> FastAPI Backend -> Text Preprocessing -> Sentiment Model -> SQLite -> API -> Frontend Dashboard
```

## Features

- Upload CSV files with product reviews
- Preprocess review text
  - lowercase conversion
  - punctuation removal
  - stopword removal
  - tokenization
- Sentiment analysis with a Hugging Face model
- Automatic fallback to a lightweight rule-based analyzer if the model cannot load
- Store results in SQLite with SQLAlchemy ORM
- View all reviews and sentiment scores
- Display positive, negative, and neutral percentages
- Simple visual sentiment distribution bars

## Database Schema

Table: `reviews`

- `id` - integer primary key
- `original_text` - original uploaded review
- `processed_text` - cleaned text after preprocessing
- `sentiment` - positive, negative, or neutral
- `score` - confidence score from 0 to 1
- `created_at` - timestamp

## CSV Format

Required column:

- `review`

Example:

```csv
id,review
1,"Great product"
2,"Very bad quality"
```

## Run Locally

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the database

This version uses SQLite, so no external database server is required. The database file is created automatically when the app starts.

Default connection string:

```env
DATABASE_URL=sqlite:///./reviews.db
```

You can export it in the shell:

```bash
export DATABASE_URL="sqlite:///./reviews.db"
```

### 4. Run the backend and frontend

The frontend is served by FastAPI as static files, so one command starts the whole app:

```bash
uvicorn backend.main:app --reload
```

Open:

- App: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Run With Docker

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000)

The SQLite database file will be stored in the project root as `reviews.db`.

## API Endpoints

- `POST /upload` - upload and process a CSV file
- `GET /reviews` - list all stored reviews
- `GET /stats` - get aggregated sentiment statistics

## Notes About the Model

- Primary model: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- On the first run, Transformers downloads the model files, so internet access is needed once unless the model is already cached.
- If the model is unavailable, the app still works with a simple fallback analyzer.

## Sample Dataset

Use [data/sample_reviews.csv](/Users/maiisovoya/Documents/New%20project/data/sample_reviews.csv) to test uploads quickly.

## Thesis-Friendly Design Choices

- Clear separation between API, services, models, and frontend
- Lightweight frontend with plain HTML, CSS, and JavaScript
- Production-style backend structure with schemas and service layer
- Simple enough to explain in a thesis presentation while still demonstrating a realistic ML pipeline
