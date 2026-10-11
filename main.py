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

Отвечай ТОЛЬКО на основе:
1. ПУЭ РК — Правила устройства электроустановок (Приказ № 230 от 20.03.2015 с изменениями)
   Официальный текст: https://adilet.zan.kz/rus/docs/V1500010851

2. ППЭЭ РК — Правила пользования электрической энергией (Приказ № 143 от 25.02.2015 с изменениями)
   Официальный текст: https://adilet.zan.kz/rus/docs/V1500010403

Обязательные правила ответа:
- Всегда старайся указать точный номер пункта, подпункта, главы, раздела или параграфа.
- Формат ссылки на норму: «согласно пункту X.X.X ПУЭ РК» или «согласно пункту XX ППЭЭ РК».
- В конце каждого ответа обязательно добавляй:
  Источник: ПУЭ РК / ППЭЭ РК
  Ссылка: https://adilet.zan.kz/rus/docs/V1500010851   (или соответствующую)
- Если точный номер пункта не знаешь — пиши «согласно требованиям главы / раздела … ПУЭ РК».
- Не выдумывай несуществующие пункты.
- Отвечай кратко, чётко и по делу.
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
