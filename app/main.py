import logging
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.Webhook import router as webhook_router
from app.routers.blobs import router as blobs_router
from app.routers.messages import router as messages_router
from app.routers.analytics import router as analytics_router
from app.routers.contacts import router as contacts_router
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

RETENTION_DAYS = 7

app = FastAPI(
    title="WhatsApp Archive API",
    description="Ingests, processes, and archives WhatsApp Business messages to Azure Blob Storage.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        settings.frontend_url,          # set FRONTEND_URL in Vercel env vars
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(blobs_router)
app.include_router(messages_router)
app.include_router(analytics_router)
app.include_router(contacts_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/purge")
async def purge_old_blobs():
    """Called daily by Vercel Cron — deletes blobs older than RETENTION_DAYS."""
    from azure.storage.blob import BlobServiceClient
    try:
        client = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
        container = client.get_container_client(settings.azure_blob_container_name)
        cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        deleted = 0
        for blob in container.list_blobs():
            if blob.last_modified and blob.last_modified < cutoff:
                container.delete_blob(blob.name)
                deleted += 1
        logger.info(f"[retention] Purged {deleted} blobs.")
        return {"status": "ok", "deleted": deleted}
    except Exception as e:
        logger.error(f"[retention] Purge failed: {e}")
        return {"status": "error", "detail": str(e)}
