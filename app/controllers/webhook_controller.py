from fastapi import Request
from app.services.message_processor import process_message
from app.config.settings import WEBHOOK_VERIFY_TOKEN

# VERIFY WEBHOOK
async def verify_webhook(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("Webhook Verified")
        return int(challenge)

    return {"error": "Verification failed ❌"}


# ✅ RECEIVE MESSAGE
async def receive_message(request: Request):

    payload = await request.json()

    print("\n📩 FULL PAYLOAD RECEIVED:")
    print(payload)

    try:
        entry = payload.get("entry", [])

        for e in entry:
            changes = e.get("changes", [])

            for change in changes:
                value = change.get("value", {})

                messages = value.get("messages", [])

                for message in messages:
                    print("\n🔥 NEW MESSAGE:")
                    print(message)

                    await process_message(message)

    except Exception as e:
        print("❌ Error:", e)

    return {"status": "received"}