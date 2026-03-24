from fastapi import FastAPI
from app.routers import webhook

app = FastAPI()

app.include_router(webhook.router)