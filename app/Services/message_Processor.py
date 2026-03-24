async def process_message(message):

    sender = message.get("from")
    msg_type = message.get("type")

    if msg_type == "text":
        text = message.get("text", {}).get("body")

        print(f"👤 Sender: {sender}")
        print(f"💬 Message: {text}")

    else:
        print(f"📦 Other message type: {msg_type}")