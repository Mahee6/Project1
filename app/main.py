import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.Webhook import router as webhook_router
from app.routers.blobs import router as blobs_router
from app.config.settings import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="WhatsApp Archive API",
    description="Ingests, processes, and archives WhatsApp Business messages to Azure Blob Storage.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(blobs_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
