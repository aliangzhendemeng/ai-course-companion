"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import create_db_and_tables
from backend.logger import setup_logging
from backend.api import chat, courses, debug, flashcards, history, progress, quiz, settings as settings_api, study_sets, summaries


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期。"""
    setup_logging()
    create_db_and_tables()
    yield


app = FastAPI(title="AI 慕课学伴", lifespan=lifespan)

# 配置 CORS，允许 Streamlit 与 Next.js 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges"],
)

app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["summaries"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(debug.router, prefix="/api/courses", tags=["debug"])
app.include_router(debug.router, prefix="/api/chat", tags=["debug"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(study_sets.router, prefix="/api/study-sets", tags=["study-sets"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["flashcards"])


@app.get("/health")
def health():
    return {"status": "ok"}
