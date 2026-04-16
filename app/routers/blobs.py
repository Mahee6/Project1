import json
import mimetypes
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
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
    
    try:
        content = blob_client.download_blob().readall()
        
        # If it's a JSON file (the metadata), return as JSON
        if path.endswith('.json'):
            try:
                return json.loads(content)
            except Exception:
                return {"raw": content.decode("utf-8", errors="replace")}
        
        # Otherwise, return as a binary response with correct MIME type
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        return Response(content=content, media_type=mime_type)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Blob not found: {str(e)}")


@router.post("/upload")
async def upload_blob(
    file: UploadFile = File(...),
    prefix: str = Query("uploads"),
    storage: AzureBlobStorage = Depends(get_storage),
):
    """Upload a file to Azure Blob Storage and return its path."""
    try:
        content = await file.read()
        # Sanitize filename
        filename = file.filename.replace(" ", "_")
        blob_path = f"{prefix}/{filename}"
        
        storage._upload_bytes(blob_path, content, content_type=file.content_type)
        
        return {
            "status": "success",
            "path": blob_path,
            "filename": filename,
            "content_type": file.content_type,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/media-proxy")
async def proxy_media(
    media_id: str = Query(...),
    storage: AzureBlobStorage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
):
    """Fetch media from WhatsApp API on-demand and cache it to blob storage."""
    import httpx
    from app.Services.media_downloader import download_media, mime_to_extension

    # First check if it's already in storage by scanning for the media_id
    container_client = storage._client.get_container_client(storage._container)
    for blob in container_client.list_blobs(name_starts_with=""):
        if f"/media/{media_id}." in blob.name:
            # Found it — serve directly
            blob_client = storage._client.get_blob_client(
                container=storage._container, blob=blob.name
            )
            content = blob_client.download_blob().readall()
            mime_type, _ = mimetypes.guess_type(blob.name)
            return Response(content=content, media_type=mime_type or "application/octet-stream")

    # Not in storage — fetch from WhatsApp
    try:
        media_bytes, mime_type = await download_media(media_id, settings.whatsapp_access_token)
        return Response(content=media_bytes, media_type=mime_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Media not available: {str(e)}")


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
