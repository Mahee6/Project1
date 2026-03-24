from fastapi import APIRouter

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(data: dict):
    
    print("Incoming data:", data)

    from app.services.message_processor import process_message
    processed = process_message(data)

    return {"status": "processed", "data": processed}