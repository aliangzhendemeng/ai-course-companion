"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import create_db_and_tables
from backend.logger import setup_logging
from backend.api import chat, courses, progress, summaries


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期。"""
    setup_logging()
    create_db_and_tables()
    yield


app = FastAPI(title="AI 慕课学伴", lifespan=lifespan)

app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["summaries"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])


@app.get("/health")
def health():
    return {"status": "ok"}
