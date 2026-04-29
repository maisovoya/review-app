from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.database import Base, engine
from backend.models.review import Review  # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Product Review Sentiment Analysis",
    description="Upload product reviews, analyze sentiment, and explore statistics.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/", include_in_schema=False)
def read_index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")
