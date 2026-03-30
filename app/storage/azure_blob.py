import json
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import AzureError


class AzureBlobStorage:
    def __init__(self, connection_string: str, container_name: str):
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container = container_name
        self._ensure_container()

    def _ensure_container(self):
        try:
            container_client = self._client.get_container_client(self._container)
            if not container_client.exists():
                container_client.create_container()
        except AzureError as e:
            raise

    def _date_prefix(self, ts: int) -> str:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y/%m/%d")

    def upload_message(self, message: dict) -> str:
        ts = message.get("timestamp", 0)
        conv_id = message.get("conversation_id", "unknown")
        msg_id = message.get("message_id", "unknown")

        blob_path = f"{self._date_prefix(ts)}/{conv_id}/messages/{msg_id}.json"
        content = json.dumps(message, ensure_ascii=False, indent=2).encode("utf-8")

        self._upload_bytes(blob_path, content, content_type="application/json")
        return blob_path

    def upload_media(
        self,
        media_bytes: bytes,
        mime_type: str,
        media_id: str,
        conversation_id: str,
        timestamp: int,
        extension: str,
    ) -> str:
        blob_path = (
            f"{self._date_prefix(timestamp)}/{conversation_id}/media/{media_id}.{extension}"
        )
        self._upload_bytes(blob_path, media_bytes, content_type=mime_type)
        return blob_path

    def _upload_bytes(self, blob_path: str, data: bytes, content_type: str):
        blob_client = self._client.get_blob_client(
            container=self._container, blob=blob_path
        )
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )
