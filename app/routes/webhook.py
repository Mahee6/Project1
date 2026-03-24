from fastapi import APIRouter, Request
from app.controllers import webhook_controller

router = APIRouter()

@router.get("/webhook")
async def verify(request: Request):
    return await webhook_controller.verify_webhook(request)


@router.post("/webhook")
async def receive(request: Request):
    return await webhook_controller.receive_message(request)