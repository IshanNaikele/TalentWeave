from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
from app.core.config import settings
from app.services.scheduler_service import scheduler
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints.candidate_portal import router as candidate_portal_router

CURRENT_DIR = Path(__file__).resolve().parent
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    print("✅ APScheduler started.")
    yield
    # Shutdown
    scheduler.shutdown()
    print("🛑 APScheduler shut down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=CURRENT_DIR / "static"), name="static")
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(candidate_portal_router, prefix="/api", tags=["Candidate Portal"])
@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API", "version": settings.VERSION}