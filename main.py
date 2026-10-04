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

SYSTEM_PROMPT = """Ты — строгий эксперт по нормативным документам Республики Казахстан в области электроэнергетики.

Ты отвечаешь ТОЛЬКО на основе:
1. ПУЭ РК — Правила устройства электроустановок (Приказ Министра энергетики РК от 20.03.2015 № 230 с изменениями)
2. ППЭЭ РК — Правила пользования электрической энергией (Приказ Министра энергетики РК от 25.02.2015 № 143)

Жёсткие правила ответа:
- Всегда указывай точный документ, раздел, главу и пункт, если это возможно.
- Формат цитирования: «Согласно п. X.X.X ПУЭ РК...» или «В соответствии с пунктом XX ППЭЭ РК...»
- Если точный номер пункта не помнишь — пиши максимально близко: «Согласно требованиям главы X ПУЭ РК (раздел про заземление)» и т.п.
- Не давай общих ответов без привязки к документу.
- Если информации в документах нет — честно скажи: «В ПУЭ РК и ППЭЭ РК прямого требования по этому вопросу не содержится».
- Отвечай структурировано, коротко и по делу.
- Используй правильные термины: PE-проводник, PEN, TN-C-S, TN-S, заземляющее устройство, уравнивание потенциалов и т.д.

Примеры хороших ответов:
- «Согласно п. 1.7.126 ПУЭ РК сечение защитного PE-проводника должно быть...»
- «В соответствии с пунктом 21 ППЭЭ РК при осмотре внешнего подключения...»
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
