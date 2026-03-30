import httpx
from typing import Optional, Dict, Any, List

WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"


class WhatsAppSender:
    def __init__(self, phone_number_id: str, access_token: str):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = WHATSAPP_API_URL.format(phone_number_id=phone_number_id)
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def send_text(
        self, to: str, text: str, preview_url: bool = False
    ) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": preview_url, "body": text},
        }
        return await self._send_request(payload)

    async def send_image(
        self, to: str, image_id: str = None, image_link: str = None, caption: str = None
    ) -> Dict[str, Any]:
        if not image_id and not image_link:
            raise ValueError("Either image_id or image_link must be provided")

        image_obj = {"caption": caption} if caption else {}
        if image_id:
            image_obj["id"] = image_id
        else:
            image_obj["link"] = image_link

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": image_obj,
        }
        return await self._send_request(payload)

    async def send_video(
        self, to: str, video_id: str = None, video_link: str = None, caption: str = None
    ) -> Dict[str, Any]:
        if not video_id and not video_link:
            raise ValueError("Either video_id or video_link must be provided")

        video_obj = {"caption": caption} if caption else {}
        if video_id:
            video_obj["id"] = video_id
        else:
            video_obj["link"] = video_link

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "video",
            "video": video_obj,
        }
        return await self._send_request(payload)

    async def send_document(
        self,
        to: str,
        document_id: str = None,
        document_link: str = None,
        caption: str = None,
        filename: str = None,
    ) -> Dict[str, Any]:
        if not document_id and not document_link:
            raise ValueError("Either document_id or document_link must be provided")

        doc_obj = {}
        if caption:
            doc_obj["caption"] = caption
        if filename:
            doc_obj["filename"] = filename
        if document_id:
            doc_obj["id"] = document_id
        else:
            doc_obj["link"] = document_link

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": doc_obj,
        }
        return await self._send_request(payload)

    async def send_audio(
        self, to: str, audio_id: str = None, audio_link: str = None
    ) -> Dict[str, Any]:
        if not audio_id and not audio_link:
            raise ValueError("Either audio_id or audio_link must be provided")

        audio_obj = {}
        if audio_id:
            audio_obj["id"] = audio_id
        else:
            audio_obj["link"] = audio_link

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": audio_obj,
        }
        return await self._send_request(payload)

    async def send_template(
        self, to: str, template_name: str, language_code: str = "en_US", components: List[Dict] = None
    ) -> Dict[str, Any]:
        template_obj = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template_obj["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template_obj,
        }
        return await self._send_request(payload)

    async def send_interactive_buttons(
        self, to: str, body_text: str, buttons: List[Dict[str, str]], header_text: str = None, footer_text: str = None
    ) -> Dict[str, Any]:
        if len(buttons) > 3:
            raise ValueError("Maximum 3 buttons allowed")

        interactive_obj = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
                    for btn in buttons
                ]
            },
        }

        if header_text:
            interactive_obj["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_obj["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_obj,
        }
        return await self._send_request(payload)

    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict],
        header_text: str = None,
        footer_text: str = None,
    ) -> Dict[str, Any]:
        interactive_obj = {
            "type": "list",
            "body": {"text": body_text},
            "action": {"button": button_text, "sections": sections},
        }

        if header_text:
            interactive_obj["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_obj["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_obj,
        }
        return await self._send_request(payload)

    async def send_location(
        self, to: str, latitude: float, longitude: float, name: str = None, address: str = None
    ) -> Dict[str, Any]:
        location_obj = {"latitude": latitude, "longitude": longitude}
        if name:
            location_obj["name"] = name
        if address:
            location_obj["address"] = address

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "location",
            "location": location_obj,
        }
        return await self._send_request(payload)

    async def send_reaction(self, to: str, message_id: str, emoji: str) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "reaction",
            "reaction": {"message_id": message_id, "emoji": emoji},
        }
        return await self._send_request(payload)

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._send_request(payload)

    async def _send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    self.base_url, json=payload, headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                return result
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except:
                    pass
                raise ValueError(f"WhatsApp API Error: {error_detail}")
            except Exception as e:
                raise
