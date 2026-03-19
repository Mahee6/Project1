from datetime import datetime, timezone


SUPPORTED_MEDIA_TYPES = {"image", "video", "audio", "document", "sticker"}


def extract_messages(payload: dict) -> list[dict]:
    normalized = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            messages = value.get("messages")
            if not messages:
                continue

            contacts = {
                c["wa_id"]: c.get("profile", {}).get("name", "")
                for c in value.get("contacts", [])
            }
            metadata = value.get("metadata", {})

            for msg in messages:
                normalized.append(_normalize(msg, contacts, metadata))

    return normalized


def _normalize(msg: dict, contacts: dict[str, str], metadata: dict) -> dict:
    sender_id = msg.get("from", "")
    msg_type = msg.get("type", "unknown")
    ts = int(msg.get("timestamp", 0))

    record = {
        "message_id": msg.get("id"),
        "conversation_id": f"conv_{sender_id}",
        "user": {
            "phone_number": sender_id,
            "display_name": contacts.get(sender_id, ""),
            "user_id": f"user_{sender_id}",
        },
        "timestamp": ts,
        "timestamp_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "message_type": msg_type,
        "receiving_phone_number_id": metadata.get("phone_number_id"),
        "raw": msg,
        "media_id": None,
        "media_mime_type": None,
        "text_body": None,
        "caption": None,
        "location": None,
        "contacts_shared": None,
        "reaction": None,
        "link_preview": None,
    }

    if msg_type == "text":
        body = msg.get("text", {}).get("body", "")
        record["text_body"] = body
        record["link_preview"] = _extract_links(body)

    elif msg_type in SUPPORTED_MEDIA_TYPES:
        media_obj = msg.get(msg_type, {})
        record["media_id"] = media_obj.get("id")
        record["media_mime_type"] = media_obj.get("mime_type")
        record["caption"] = media_obj.get("caption")

    elif msg_type == "location":
        loc = msg.get("location", {})
        record["location"] = {
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "name": loc.get("name"),
            "address": loc.get("address"),
        }

    elif msg_type == "contacts":
        record["contacts_shared"] = msg.get("contacts", [])

    elif msg_type == "reaction":
        reaction = msg.get("reaction", {})
        record["reaction"] = {
            "message_id": reaction.get("message_id"),
            "emoji": reaction.get("emoji"),
        }

    elif msg_type == "interactive":
        record["text_body"] = str(msg.get("interactive", {}))

    elif msg_type == "button":
        record["text_body"] = msg.get("button", {}).get("text")

    elif msg_type == "order":
        record["text_body"] = str(msg.get("order", {}))

    return record


def _extract_links(text: str) -> list[str]:
    import re
    return re.compile(r"https?://\S+").findall(text)
