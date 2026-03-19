import json
from fastapi import APIRouter, Depends, Query
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
