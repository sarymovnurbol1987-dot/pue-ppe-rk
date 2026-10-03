from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx

app = FastAPI(title="ПУЭ / ППЭЭ РК AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Ты — опытный эксперт по электроустановкам Республики Казахстан.
Твоя задача — отвечать на вопросы строго на основе действующих нормативных документов РК:

1. ПУЭ РК — Правила устройства электроустановок 
   (Приказ Министра энергетики РК от 20 марта 2015 года № 230 с изменениями).

2. ППЭЭ РК — Правила пользования электрической энергией 
   (Приказ Министра энергетики РК от 25 февраля 2015 года № 143).

Правила ответа:
- Отвечай четко, по делу, на русском языке.
- Всегда указывай, из какого документа взята информация.
- Если вопрос не относится к этим правилам — вежливо скажи об этом.
- Не выдумывай требования, которых нет в нормах.
"""

@app.get("/")
def root():
    return {"status": "ok", "message": "ПУЭ / ППЭЭ РК AI Assistant работает"}

@app.post("/chat")
async def chat(req: ChatRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API-ключ не настроен. Укажи OPENAI_API_KEY в переменных окружения."
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message}
    ]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1200
                }
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        return {
            "answer": answer,
            "source": "ПУЭ РК / ППЭЭ РК"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))