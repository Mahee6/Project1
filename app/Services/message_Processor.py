def process_message(data):
    try:
        if "entry" not in data:
            return {"error": "Invalid payload"}

        message = data["entry"][0]["changes"][0]["value"]["messages"][0]

        user = message.get("from", "unknown")
        msg_type = message.get("type", "unknown")

        result = {
            "user": user,
            "type": msg_type
        }

        if msg_type == "text":
            result["message"] = message.get("text", {}).get("body", "")

        elif msg_type == "image":
            result["media_id"] = message.get("image", {}).get("id", "")
            result["media_type"] = "image"

        elif msg_type == "video":
            result["media_id"] = message.get("video", {}).get("id", "")
            result["media_type"] = "video"

        else:
            result["message"] = "unsupported type"

        return result

    except Exception as e:
        return {
            "error": "processing failed",
            "details": str(e)
        }