from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.settings import router as settings_router
from app.api.gmail import router as gmail_router
from app.api.ai import router as ai_router
from app.api.tasks import router as tasks_router
from app.api.telegram_cron import router as telegram_cron_router

app = FastAPI(title="AI Accountability Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.scheduler import start_scheduler

@app.on_event("startup")
async def on_startup():
    await init_db()
    start_scheduler()

app.include_router(auth_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(gmail_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(telegram_cron_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI Accountability Assistant API is running"}
