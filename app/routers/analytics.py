from fastapi import APIRouter, Depends, Query
from app.config.settings import Settings, get_settings
from app.storage.azure_blob import AzureBlobStorage
from app.Services.analytics_service import AnalyticsService
import json

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_storage(settings: Settings = Depends(get_settings)) -> AzureBlobStorage:
    return AzureBlobStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_blob_container_name,
    )


@router.get("/summary")
def get_summary(
    prefix: str = Query("", description="Filter by date prefix (e.g., '2024/03')"),
    storage: AzureBlobStorage = Depends(get_storage),
):
    container_client = storage._client.get_container_client(storage._container)
    
    messages = []
    for blob in container_client.list_blobs(name_starts_with=prefix or None):
        if blob.name.endswith(".json") and "/messages/" in blob.name:
            try:
                blob_client = storage._client.get_blob_client(
                    container=storage._container, blob=blob.name
                )
                content = blob_client.download_blob().readall()
                msg = json.loads(content)
                messages.append(msg)
            except Exception as e:
                pass

    analytics = AnalyticsService()
    stats = analytics.analyze_messages(messages)
    
    return {
        "prefix": prefix or "all",
        "statistics": stats,
    }


@router.get("/conversation/{conversation_id}")
def get_conversation_analytics(
    conversation_id: str,
    storage: AzureBlobStorage = Depends(get_storage),
):
    container_client = storage._client.get_container_client(storage._container)
    
    messages = []
    for blob in container_client.list_blobs():
        if conversation_id in blob.name and blob.name.endswith(".json") and "/messages/" in blob.name:
            try:
                blob_client = storage._client.get_blob_client(
                    container=storage._container, blob=blob.name
                )
                content = blob_client.download_blob().readall()
                msg = json.loads(content)
                messages.append(msg)
            except Exception as e:
                pass

    analytics = AnalyticsService()
    summary = analytics.get_conversation_summary(messages, conversation_id)
    
    return summary


@router.get("/user/{phone_number}")
def get_user_analytics(
    phone_number: str,
    storage: AzureBlobStorage = Depends(get_storage),
):
    container_client = storage._client.get_container_client(storage._container)
    
    messages = []
    for blob in container_client.list_blobs():
        if blob.name.endswith(".json") and "/messages/" in blob.name:
            try:
                blob_client = storage._client.get_blob_client(
                    container=storage._container, blob=blob.name
                )
                content = blob_client.download_blob().readall()
                msg = json.loads(content)
                if msg.get("user", {}).get("phone_number") == phone_number:
                    messages.append(msg)
            except Exception as e:
                pass

    analytics = AnalyticsService()
    activity = analytics.get_user_activity(messages, phone_number)
    
    return activity
