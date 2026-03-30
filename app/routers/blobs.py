import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.config.settings import Settings, get_settings
from app.storage.azure_blob import AzureBlobStorage

router = APIRouter(prefix="/blobs", tags=["blobs"])


def get_storage(settings: Settings = Depends(get_settings)) -> AzureBlobStorage:
    return AzureBlobStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_blob_container_name,
    )


@router.get("")
def list_blobs(
    prefix: str = Query(""),
    storage: AzureBlobStorage = Depends(get_storage),
):
    container_client = storage._client.get_container_client(storage._container)
    blobs = [
        {"name": b.name, "size": b.size, "last_modified": str(b.last_modified)}
        for b in container_client.list_blobs(name_starts_with=prefix or None)
    ]
    return {"count": len(blobs), "blobs": blobs}


@router.get("/content")
def get_blob_content(
    path: str = Query(...),
    storage: AzureBlobStorage = Depends(get_storage),
):
    blob_client = storage._client.get_blob_client(
        container=storage._container, blob=path
    )
    content = blob_client.download_blob().readall()
    try:
        return json.loads(content)
    except Exception:
        return {"raw": content.decode("utf-8", errors="replace")}


class DeleteMessageRequest(BaseModel):
    path: str  # blob path of the message JSON


@router.delete("")
def delete_message(
    body: DeleteMessageRequest,
    storage: AzureBlobStorage = Depends(get_storage),
):
    """Delete a message blob and its associated media blob (if any)."""
    try:
        # Read the message to find any linked media
        blob_client = storage._client.get_blob_client(
            container=storage._container, blob=body.path
        )
        try:
            content = blob_client.download_blob().readall()
            msg = json.loads(content)
            media_id = msg.get("media_id")
            conversation_id = msg.get("conversation_id")
            timestamp = msg.get("timestamp", 0)
        except Exception:
            media_id = None

        # Delete the message JSON blob
        blob_client.delete_blob()

        # Delete associated media blob if present
        deleted_media = False
        if media_id and conversation_id and timestamp:
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            date_prefix = dt.strftime("%Y/%m/%d")
            # Try common extensions
            for ext in ["jpg", "png", "mp4", "ogg", "mp3", "pdf", "webp", "3gp", "m4a", "bin"]:
                media_path = f"{date_prefix}/{conversation_id}/media/{media_id}.{ext}"
                try:
                    media_client = storage._client.get_blob_client(
                        container=storage._container, blob=media_path
                    )
                    media_client.delete_blob()
                    deleted_media = True
                    break
                except Exception:
                    continue

        return {"status": "deleted", "path": body.path, "media_deleted": deleted_media}

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to delete: {str(e)}")
