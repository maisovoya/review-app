import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.review import ReviewOut, StatsOut, UploadResponse
from backend.services.review_service import (
    calculate_sentiment_stats,
    create_review_records,
    fetch_reviews,
)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_reviews(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    if "review" not in (reader.fieldnames or []):
        raise HTTPException(
            status_code=400,
            detail='CSV must contain a "review" column.',
        )

    rows = [row for row in reader if row.get("review")]
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    inserted = create_review_records(db, rows)
    return UploadResponse(message="Reviews uploaded and processed successfully.", count=inserted)


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(db: Session = Depends(get_db)):
    return fetch_reviews(db)


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return calculate_sentiment_stats(db)
