from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import time

from app.config.settings import Settings, get_settings
from app.Services.whatsapp_sender import WhatsAppSender
from app.storage.azure_blob import AzureBlobStorage

router = APIRouter(prefix="/messages", tags=["messages"])


def get_sender(settings: Settings = Depends(get_settings)) -> WhatsAppSender:
    return WhatsAppSender(
        phone_number_id=settings.whatsapp_phone_number_id,
        access_token=settings.whatsapp_access_token,
    )


def get_storage(settings: Settings = Depends(get_settings)) -> AzureBlobStorage:
    return AzureBlobStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_blob_container_name,
    )


class TextMessageRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number with country code")
    text: str = Field(..., description="Message text")
    preview_url: bool = Field(False, description="Enable URL preview")


class MediaMessageRequest(BaseModel):
    to: str
    media_id: Optional[str] = None
    media_link: Optional[str] = None
    caption: Optional[str] = None


class DocumentMessageRequest(BaseModel):
    to: str
    document_id: Optional[str] = None
    document_link: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None


class TemplateMessageRequest(BaseModel):
    to: str
    template_name: str
    language_code: str = "en_US"
    components: Optional[List[Dict]] = None


class ButtonMessageRequest(BaseModel):
    to: str
    body_text: str
    buttons: List[Dict[str, str]] = Field(..., max_length=3)
    header_text: Optional[str] = None
    footer_text: Optional[str] = None


class ListMessageRequest(BaseModel):
    to: str
    body_text: str
    button_text: str
    sections: List[Dict]
    header_text: Optional[str] = None
    footer_text: Optional[str] = None


class LocationMessageRequest(BaseModel):
    to: str
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


class ReactionRequest(BaseModel):
    to: str
    message_id: str
    emoji: str


class MarkReadRequest(BaseModel):
    message_id: str


@router.post("/text", status_code=status.HTTP_200_OK)
async def send_text_message(
    request: TextMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
    storage: AzureBlobStorage = Depends(get_storage),
):
    try:
        result = await sender.send_text(
            to=request.to, text=request.text, preview_url=request.preview_url
        )
        
        sent_message = {
            "message_id": result.get("messages", [{}])[0].get("id", f"sent_{int(time.time())}"),
            "conversation_id": f"conv_{request.to}",
            "user": None,
            "timestamp": int(time.time()),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "message_type": "text",
            "text_body": request.text,
            "receiving_phone_number_id": None,
            "raw": result,
            "media_id": None,
            "media_mime_type": None,
            "caption": None,
            "location": None,
            "contacts_shared": None,
            "reaction": None,
            "link_preview": None,
        }
        
        storage.upload_message(sent_message)
        
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.post("/image", status_code=status.HTTP_200_OK)
async def send_image_message(
    request: MediaMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
    storage: AzureBlobStorage = Depends(get_storage),
):
    try:
        result = await sender.send_image(
            to=request.to,
            image_id=request.media_id,
            image_link=request.media_link,
            caption=request.caption,
        )
        
        sent_message = {
            "message_id": result.get("messages", [{}])[0].get("id", f"sent_{int(time.time())}"),
            "conversation_id": f"conv_{request.to}",
            "user": None,
            "timestamp": int(time.time()),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "message_type": "image",
            "text_body": None,
            "caption": request.caption,
            "receiving_phone_number_id": None,
            "raw": result,
            "media_id": request.media_id,
            "media_mime_type": None,
            "location": None,
            "contacts_shared": None,
            "reaction": None,
            "link_preview": None,
        }
        
        storage.upload_message(sent_message)
        
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send image: {str(e)}",
        )


@router.post("/video", status_code=status.HTTP_200_OK)
async def send_video_message(
    request: MediaMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
    storage: AzureBlobStorage = Depends(get_storage),
):
    try:
        result = await sender.send_video(
            to=request.to,
            video_id=request.media_id,
            video_link=request.media_link,
            caption=request.caption,
        )
        
        sent_message = {
            "message_id": result.get("messages", [{}])[0].get("id", f"sent_{int(time.time())}"),
            "conversation_id": f"conv_{request.to}",
            "user": None,
            "timestamp": int(time.time()),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "message_type": "video",
            "text_body": None,
            "caption": request.caption,
            "receiving_phone_number_id": None,
            "raw": result,
            "media_id": request.media_id,
            "media_mime_type": None,
            "location": None,
            "contacts_shared": None,
            "reaction": None,
            "link_preview": None,
        }
        
        storage.upload_message(sent_message)
        
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send video: {str(e)}",
        )


@router.post("/document", status_code=status.HTTP_200_OK)
async def send_document_message(
    request: DocumentMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.send_document(
            to=request.to,
            document_id=request.document_id,
            document_link=request.document_link,
            caption=request.caption,
            filename=request.filename,
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send document: {str(e)}",
        )


@router.post("/audio", status_code=status.HTTP_200_OK)
async def send_audio_message(
    request: MediaMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.send_audio(
            to=request.to, audio_id=request.media_id, audio_link=request.media_link
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send audio: {str(e)}",
        )


@router.post("/template", status_code=status.HTTP_200_OK)
async def send_template_message(
    request: TemplateMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.send_template(
            to=request.to,
            template_name=request.template_name,
            language_code=request.language_code,
            components=request.components,
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send template: {str(e)}",
        )


@router.post("/interactive/buttons", status_code=status.HTTP_200_OK)
async def send_button_message(
    request: ButtonMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.send_interactive_buttons(
            to=request.to,
            body_text=request.body_text,
            buttons=request.buttons,
            header_text=request.header_text,
            footer_text=request.footer_text,
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send button message: {str(e)}",
        )


@router.post("/interactive/list", status_code=status.HTTP_200_OK)
async def send_list_message(
    request: ListMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.send_interactive_list(
            to=request.to,
            body_text=request.body_text,
            button_text=request.button_text,
            sections=request.sections,
            header_text=request.header_text,
            footer_text=request.footer_text,
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send list message: {str(e)}",
        )


@router.post("/location", status_code=status.HTTP_200_OK)
async def send_location_message(
    request: LocationMessageRequest,
    sender: WhatsAppSender = Depends(get_sender),
    storage: AzureBlobStorage = Depends(get_storage),
):
    try:
        result = await sender.send_location(
            to=request.to,
            latitude=request.latitude,
            longitude=request.longitude,
            name=request.name,
            address=request.address,
        )
        
        sent_message = {
            "message_id": result.get("messages", [{}])[0].get("id", f"sent_{int(time.time())}"),
            "conversation_id": f"conv_{request.to}",
            "user": None,
            "timestamp": int(time.time()),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "message_type": "location",
            "text_body": None,
            "caption": None,
            "receiving_phone_number_id": None,
            "raw": result,
            "media_id": None,
            "media_mime_type": None,
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "name": request.name,
                "address": request.address,
            },
            "contacts_shared": None,
            "reaction": None,
            "link_preview": None,
        }
        
        storage.upload_message(sent_message)
        
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send location: {str(e)}",
        )


@router.post("/reaction", status_code=status.HTTP_200_OK)
async def send_reaction(
    request: ReactionRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.send_reaction(
            to=request.to, message_id=request.message_id, emoji=request.emoji
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reaction: {str(e)}",
        )


@router.post("/mark-read", status_code=status.HTTP_200_OK)
async def mark_message_read(
    request: MarkReadRequest,
    sender: WhatsAppSender = Depends(get_sender),
):
    try:
        result = await sender.mark_as_read(message_id=request.message_id)
        return {"status": "marked_read", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark as read: {str(e)}",
        )
