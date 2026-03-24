from fastapi import FastAPI
from app.routes import webhook

app = FastAPI(title="WhatsApp Collector")

app.include_router(webhook.router)

@app.get("/")
def home():
    return {"message": "API Running 🚀"}