from random import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import List
import json

app = FastAPI(title="Gift Finding Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessages(BaseModel):
    message: str
    conversation_id: str = "default"

class GiftSuggestion(BaseModel):
    gift: str
    reason: str
    price_range: str

class ChatResponse(BaseModel):
    reply: str
    suggestions: List[str] = []
    gifts: List[GiftSuggestion] = []

async def get_openrouter_response(prompt: str) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "Bearer free",
            "Content-Type": "application/json"
        }

        data = {
            "model": "openrouter:meta-llama/llama-3.2-3b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": "you are a helpful assistant that suggests gifts based on user input. "
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            resp_json = response.json()
            return resp_json['choices'][0]['message']['content']
        else:
            return get_fallback_response()
    
    except Exception as e:
        return get_fallback_response()
    
def get_fallback_response() -> str:
    fallbacks = [
        """Here are some gift suggestions:
        1. Gift Name: Personalized Mug
        Reason: A personalized mug with a custom message or photo is a thoughtful gift that shows you care.
        Price Range: Rs300 - Rs700
        2. Gift Name: Scented Candles
        Reason: Scented candles create a relaxing atmosphere and are perfect for unwinding after a
        long day.
        Price Range: Rs200 - Rs500
        3. Gift Name: Indoor Plant
        Reason: An indoor plant adds a touch of nature to any space and is great for improving air quality.
        Price Range: Rs400 - Rs1000
        """,
        """Here are some gift suggestions:
        1. Gift Name: Customized Photo Album
        Reason: A photo album filled with cherished memories is a heartfelt gift that captures special moments.
        Price Range: Rs500 - Rs1500
        2. Gift Name: Gourmet Chocolate Box
        Reason: A box of gourmet chocolates is a delicious treat that anyone would appreciate.
        Price Range: Rs300 - Rs800
        3. Gift Name: Fitness Tracker
        Reason: A fitness tracker is a practical gift for someone who enjoys staying active and healthy.
        Price Range: Rs1500 - Rs3000
        """
    ]
    return random.choice(fallbacks)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessages):
    try:
        prompt = f"""User is looking for gift suggestions based on the following message:
        "{chat_message.message}"
        Please provide 3 gift suggestions with the following details for each:
        1. Gift Name
        2. Reason why it's a good gift
        3. Price Range
        """

        airesponse = await get_openrouter_response(prompt)

        gifts = parse_gift_suggestions(airesponse)
        suggestions = generate_suggestions(chat_message.message, airesponse)
        return ChatResponse(reply=airesponse, suggestions=suggestions[:5], gifts=gifts[:3])

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def parse_gift_suggestions(response: str) -> List[GiftSuggestion]:
    gifts = []
    lines = response.split('\n')

    current_gift = None
    current_reason = None
    current_price = None

    for line in lines:
        line_lower = line.lower()
        if 'gift name:' in line_lower or 'gift:' in line_lower:
            if current_gift and current_reason:
                gifts.append(GiftSuggestion(
                    gift=current_gift,
                    reason=current_reason,
                    price_range=current_price or "Not specified"
                ))
            
            parts = line.split(":")
            if len(parts) > 1:
                current_gift = parts[1].strip()
            elif 'why' in line_lower and ('good' in line_lower or 'reason' in line_lower):
                parts = line.split(":")
                if len(parts) > 1:
                    current_reason = parts[1].strip()
            elif 'price' in line_lower or 'budget' in line_lower:
                parts = line.split(":")
                if len(parts) > 1:
                    current_price = parts[1].strip()
    
    if current_gift and current_reason:
        gifts.append(GiftSuggestion(
            gift=current_gift,
            reason=current_reason,
            price_range=current_price or "Not specified"
        ))
    
    return gifts[:3]

def generate_suggestions(user_message: str, ai_response: str) -> List[str]:
    suggestions = []

    base_suggestions = [
        "for my mother's birthday",
        "for a tech enthusiast",
        "anniversary gift ideas",
        "gifts under Rs500",
        "unique handmade gifts",
    ]

    if 'birthday' in user_message.lower():
        suggestions.extend(["suitable birthday gifts", "personalized birthday presents", "birthday gift ideas for him/her"])
    if 'diwali' in user_message.lower():
        suggestions.extend(["top Diwali gifts", "Diwali gift ideas for family", "budget-friendly Diwali presents"])
    if 'festival' in user_message.lower():
        suggestions.extend(["festival gift ideas", "traditional festival presents", "gifts for festive occasions"])

    suggestions.extend(base_suggestions)

    return list(set(suggestions))[:5]

@app.get("/")
async def root():
    return {"message": "Gift Finding Chatbot API is running."}

@app.get("/health")
async def health():
    return {"status": "healthy"}

