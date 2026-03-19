import logging
import httpx

logger = logging.getLogger(__name__)

WHATSAPP_MEDIA_URL = "https://graph.facebook.com/v19.0/{media_id}"


async def download_media(media_id: str, access_token: str) -> tuple[bytes, str]:
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        meta_resp = await client.get(
            WHATSAPP_MEDIA_URL.format(media_id=media_id),
            headers=headers,
        )
        meta_resp.raise_for_status()
        meta = meta_resp.json()

        download_url: str = meta["url"]
        mime_type: str = meta.get("mime_type", "application/octet-stream")

        logger.info("Downloading media %s (%s)", media_id, mime_type)

        media_resp = await client.get(download_url, headers=headers)
        media_resp.raise_for_status()

    return media_resp.content, mime_type


def mime_to_extension(mime_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "video/mp4": "mp4",
        "video/3gpp": "3gp",
        "audio/ogg": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp4": "m4a",
        "application/pdf": "pdf",
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
        "image/gif": "gif",
        "video/quicktime": "mov",
    }
    return mapping.get(mime_type, "bin")
