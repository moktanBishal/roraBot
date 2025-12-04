from fastapi import FastAPI, Request, Response
from openai import OpenAI
import requests
import os
app = FastAPI()

# Load from environment variables (Railway/Vercel/Render will have these set)
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "truman_cs_2018_capstone")

# Choose your LLM backend here
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise Exception("ERROR: GROQ_API_KEY is missing! Add it in Railway Variables.")

client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)
MODEL = "llama-3.1-70b-versatile"

SYSTEM_PROMPT = """
You are Nepal Europe Job Assistant. 
Answer ONLY in Nepali if the user writes in Nepali, otherwise simple English.
Give accurate December 2025 guidance for Germany Chancenkarte, Portugal Job Seeker Visa, Croatia/Malta/Poland/Romania work permits, care worker programs, etc.
Always warn about scams, recommend only official sources, and tell users to verify with embassy websites.
Be encouraging but realistic. Keep replies concise and helpful.
"""

@app.get("/webhook")
async def verify(request: Request):
    if request.query_params.get("hub.mode") == "subscribe" and \
       request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=request.query_params.get("hub.challenge"))
    return "Forbidden", 403

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for message in messages:
                if message.get("type") != "text":
                    continue
                    
                user_phone = message["from"]
                user_text = message["text"]["body"]
                
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_text}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    bot_reply = response.choices[0].message.content
                except Exception as e:
                    bot_reply = "माफ गर्नुहोस्, अहिले धेरै म्यासेज आएको छ। १ मिनेटपछि फेरि प्रयास गर्नुहोस्।"
                
                # Send reply
                url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
                headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
                payload = {
                    "messaging_product": "whatsapp",
                    "to": user_phone,
                    "type": "text",
                    "text": {"body": bot_reply}
                }
                requests.post(url, json=payload, headers=headers)
    
    return {"status": "ok"}

# Health check for Railway/Render
@app.get("/")
async def root():
    return {"status": "Nepal Europe Job Bot is running – Truman State CS Capstone 2025"}
