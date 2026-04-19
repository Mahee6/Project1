WhatsApp Archive API 

A FastAPI backend that receives WhatsApp Business messages via webhook, processes them, and stores them in Azure Blob Storage. It also provides APIs for sending messages, analytics, and contact management. The project is deployed using Vercel. 

 

Project Overview 

This project is designed to store and manage WhatsApp messages in a scalable way without using any database. 

It: 

Receives messages from WhatsApp Cloud API  

Processes and cleans the data  

Stores messages and media in Azure Blob Storage  

Provides APIs to send messages and analyze data  

It converts raw WhatsApp data into a structured storage system. 

 

🎯 Goals 

Build a webhook system to receive WhatsApp messages  

Store messages without using a database  

Handle media files like images, videos, and documents  

Provide APIs for sending messages and viewing data  

Deploy using a serverless architecture  

 

⚙️ Tech Stack 

Python (FastAPI)  

Azure Blob Storage  

WhatsApp Cloud API  

Vercel  

httpx  

 

 

🔄 How It Works 

WhatsApp sends messages to /webhook  

The system verifies the request for security  

The message is processed and converted into a clean JSON format  

The JSON is stored in Azure Blob Storage  

If media is present, it is downloaded and stored separately  

 
 

 

☁️ Storage 

All data is stored in Azure Blob Storage in a structured format: 

whatsapp-messages/ 
 YYYY/MM/DD/ 
   conv_{phone}/ 
     messages/ 
     media/ 

 

Features 

Receive WhatsApp messages  

Send text and media messages  

Store and retrieve messages  

Manage contacts  

View analytics  

 

API Overview 

/webhook → receive messages  

/messages/* → send messages  

/blobs → manage stored data  

/analytics → view stats  

/contacts → manage users  

 

 Run Locally 

pip install -r requirements.txt 
uvicorn app.main:app --reload
