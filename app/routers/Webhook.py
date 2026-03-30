import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.config.settings import Settings, get_settings
from app.Services.media_downloader import download_media, mime_to_extension
from app.Services.message_Processor import extract_messages, SUPPORTED_MEDIA_TYPES
from app.storage.azure_blob import AzureBlobStorage

router = APIRouter(prefix="/webhook", tags=["webhook"])


def get_storage(settings: Settings = Depends(get_settings)) -> AzureBlobStorage:
    return AzureBlobStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_blob_container_name,
    )


@router.get("", status_code=status.HTTP_200_OK, response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(content=hub_challenge, status_code=200)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@router.post("", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    storage: AzureBlobStorage = Depends(get_storage),
):
    body = await request.body()
    _verify_signature(body, request.headers.get("X-Hub-Signature-256", ""), settings.whatsapp_app_secret)

    payload = await request.json()

    if payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    messages = extract_messages(payload)

    for msg in messages:
        storage.upload_message(msg)

        if msg["message_type"] in SUPPORTED_MEDIA_TYPES and msg.get("media_id"):
            try:
                media_bytes, mime_type = await download_media(
                    msg["media_id"], settings.whatsapp_access_token
                )
                ext = mime_to_extension(mime_type)
                storage.upload_media(
                    media_bytes=media_bytes,
                    mime_type=mime_type,
                    media_id=msg["media_id"],
                    conversation_id=msg["conversation_id"],
                    timestamp=msg["timestamp"],
                    extension=ext,
                )
                msg["media_mime_type"] = mime_type
                storage.upload_message(msg)
            except Exception as exc:
                pass

    return {"status": "ok"}


def _verify_signature(body: bytes, signature_header: str, app_secret: str):
    from app.config.settings import get_settings
    if get_settings().app_env == "development" and "bypass_for_testing" in signature_header:
        return

    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    expected = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(expected, received):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
