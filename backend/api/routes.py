import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.review import (
    CollectRequest,
    DeleteResponse,
    InsightsOut,
    ProblemsOut,
    ReviewOut,
    StatsOut,
    UploadResponse,
)
from backend.services.insights import generate_insights
from backend.services.marketplaces import get_marketplace_client
from backend.services.review_service import (
    calculate_sentiment_stats,
    delete_review,
    fetch_reviews,
    get_top_problems,
    normalize_csv_reviews,
    save_reviews,
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

    inserted = save_reviews(db, normalize_csv_reviews(rows))
    return UploadResponse(message="Reviews uploaded and processed successfully.", count=inserted)


@router.post("/collect", response_model=UploadResponse)
def collect_reviews(payload: CollectRequest, db: Session = Depends(get_db)):
    try:
        client = get_marketplace_client(payload.marketplace)
        collected_reviews = client.fetch_reviews(
            product_id=payload.product_id,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        inserted = save_reviews(db, collected_reviews)
    except NotImplementedError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Marketplace collection failed: {error}",
        ) from error

    return UploadResponse(
        message="Marketplace reviews collected and processed successfully.",
        count=inserted,
    )


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(db: Session = Depends(get_db)):
    return fetch_reviews(db)


@router.delete("/reviews/{review_id}", response_model=DeleteResponse)
def remove_review(review_id: int, db: Session = Depends(get_db)):
    deleted = delete_review(db, review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found.")

    return DeleteResponse(message="Review deleted successfully")


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return calculate_sentiment_stats(db)


@router.get("/problems", response_model=ProblemsOut)
def get_problems(db: Session = Depends(get_db)):
    return get_top_problems(db)


@router.get("/insights", response_model=InsightsOut)
def get_insights(db: Session = Depends(get_db)):
    stats = calculate_sentiment_stats(db)
    problems = get_top_problems(db)
    return generate_insights(stats, problems)
