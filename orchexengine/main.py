"""OrchexEngine - OpenAI-compatible LLM orchestration layer"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes import router as chat_router
from .api.metrics import router as metrics_router
from .telemetry.middleware import TelemetryMiddleware
from .database.session import init_db
from .utils.config import get_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup: Initialize database tables
    init_db()
    yield
    # Shutdown: cleanup if needed


# Create FastAPI app
app = FastAPI(
    title="OrchexEngine",
    description="OpenAI-compatible LLM orchestration layer with intelligent routing",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add telemetry middleware
app.add_middleware(TelemetryMiddleware)

# Include routers
app.include_router(chat_router)  # /v1/chat/completions
app.include_router(metrics_router)  # /metrics/*


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "OrchexEngine"}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}
