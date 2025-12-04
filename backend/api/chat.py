from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_ai import Agent
import os
from typing import List, Dict, Any
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

agent = Agent(
    'openrouter:meta-llama/llama-3.2-3b-instruct:free',
    model_tools=[],
)

conversations = {}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessages):
    try:
        conv_id = chat_message.conversation_id
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        conversations[conv_id].append({"role": "user", "content": chat_message.message})
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversations[conv_id][-5:]])
        prompt = f""" You are a helpful assistant that suggests gifts based on user input.
        Conversation History:
        {context}

        Users Last Message: {chat_message.message}

        Your task: 
        1. Answer Questions
        2. Suggest 3 gift ideas relevant to the user's input.
        3. Keep your response concise and relevant friendly and helpful.
        4. Format gift suggestion as:
        Gift Name: <name>
        Reason: <reason>
        Price Range: <price range>
        If this is the first message, greet the user and ask for more details about the recipient.
        """

        result = await agent.run(prompt)
        ai_response = str(result.data)

        gifts = parse_gift_suggestions(ai_response)
        suggestions = generate_suggestions(chat_message.message, ai_response)
        conversations[conv_id].append({"role": "assistant", "content": ai_response})

        if len(conversations[conv_id]) > 10:
            conversations[conv_id] = conversations[conv_id][-10:]

        return ChatResponse(reply=ai_response, suggestions=suggestions, gifts=gifts)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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

