import os
import io
import uuid
import mimetypes
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from utils.cm_functions import appointment_gpt, insurance_gpt, appointment_gpt_ru, insurance_gpt_ru
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Text-Response"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
executor = ThreadPoolExecutor(max_workers=4)

VOICE_CONFIG = {
    "indian_male": {
        "voice": "echo",
        "instructions": "Speak like a real human with a natural Indian English accent. Use warm, conversational tone. Speak smoothly with natural pauses and rhythm. Avoid robotic or monotone delivery."
    },
    "indian_female": {
        "voice": "shimmer",
        "instructions": "Speak like a real human with a natural Indian English accent. Use warm, friendly and conversational tone. Speak smoothly with natural pauses and rhythm. Avoid robotic or monotone delivery."
    },
    "american_male": {
        "voice": "onyx",
        "instructions": "Speak like a real human with a natural American English accent. Use warm, conversational tone. Speak smoothly with natural pauses and rhythm. Avoid robotic or monotone delivery."
    },
    "american_female": {
        "voice": "nova",
        "instructions": "Speak like a real human with a natural American English accent. Use warm, friendly and conversational tone. Speak smoothly with natural pauses and rhythm. Avoid robotic or monotone delivery."
    },
}


BOT_CONFIG = {
    "appointment":    {"greeting": "Hi, this is the Healthcare Center. How can I help you?",          "handler": appointment_gpt},
    "appointment_ru": {"greeting": "Привет, это медицинский центр. Как я могу вам помочь?",           "handler": appointment_gpt_ru},
    "insurance":      {"greeting": "Hello! This is the Insurance Assistance Center. How can I assist you?", "handler": insurance_gpt},
    "insurance_ru":   {"greeting": "Здравствуйте! Это центр страховой поддержки. Как я могу вам помочь?",  "handler": insurance_gpt_ru},
}
async def speech_to_text(file_path: str, language: str = "en") -> str:
    loop = asyncio.get_event_loop()
    def _transcribe():
        mime_type = mimetypes.guess_type(file_path)[0] or "audio/mpeg"
        with open(file_path, "rb") as audio_file:
            return client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe-2025-03-20",

                file=(os.path.basename(file_path), audio_file, mime_type),
                language=language
            ).text
    return await loop.run_in_executor(executor, _transcribe)

async def text_to_speech(text: str, voice: str, instructions: str = "") -> io.BytesIO:
    loop = asyncio.get_event_loop()
    def _synthesize():
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts-2025-03-20",

            voice=voice,
            input=text,
            instructions=instructions,
            speed=0.85
        )
        return io.BytesIO(response.read())
    return await loop.run_in_executor(executor, _synthesize)


@app.get("/")
async def root():
    return {"message": "Voice AI API Ready ✅", "bots": list(BOT_CONFIG.keys()), "voices": list(VOICE_CONFIG.keys())}

@app.get("/greeting/{bot_type}")
async def get_greeting(bot_type: str, voice_type: str = Query("american_female")):
    if bot_type not in BOT_CONFIG:
        return JSONResponse(content={"error": f"Invalid bot. Available: {list(BOT_CONFIG.keys())}"}, status_code=400)
    if voice_type not in VOICE_CONFIG:
        return JSONResponse(content={"error": f"Invalid voice. Available: {list(VOICE_CONFIG.keys())}"}, status_code=400)

    config = BOT_CONFIG[bot_type]
    vc = VOICE_CONFIG[voice_type]
    print(f"👋 [{bot_type}] [{voice_type}] Greeting: {config['greeting']}")

    audio_buffer = await text_to_speech(config["greeting"], vc["voice"], vc["instructions"])
    audio_buffer.seek(0)
    encoded_text = base64.b64encode(config["greeting"].encode("utf-8")).decode("ascii")

    return StreamingResponse(audio_buffer, media_type="audio/mpeg", headers={"X-Text-Response": encoded_text})

@app.post("/chat")
async def unified_chat(
    file: UploadFile = File(...),
    bot_type: str = Query(...),
    voice_type: str = Query("american_female"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if bot_type not in BOT_CONFIG:
        return JSONResponse(content={"error": f"Invalid bot. Available: {list(BOT_CONFIG.keys())}"}, status_code=400)
    if voice_type not in VOICE_CONFIG:
        return JSONResponse(content={"error": f"Invalid voice. Available: {list(VOICE_CONFIG.keys())}"}, status_code=400)

    try:
        config = BOT_CONFIG[bot_type]
        vc = VOICE_CONFIG[voice_type]
        unique_id = uuid.uuid4().hex
        temp_audio = f"temp_{unique_id}_{bot_type}.wav"

        language = "ru" if "_ru" in bot_type else "en"

        content = await file.read()
        with open(temp_audio, "wb") as f:
            f.write(content)

        user_text = await speech_to_text(temp_audio, language)
        user_text = user_text.strip() or "Silent audio detected"
        print(f"🧑 [{bot_type}] User: {user_text}")

        loop = asyncio.get_event_loop()
        bot_reply = await loop.run_in_executor(executor, config["handler"], user_text)
        print(f"🤖 [{bot_type}] Bot: {bot_reply}")

        audio_buffer = await text_to_speech(bot_reply, vc["voice"], vc["instructions"])

        background_tasks.add_task(os.remove, temp_audio)
        encoded_reply = base64.b64encode(bot_reply.encode("utf-8")).decode("ascii")

        return StreamingResponse(audio_buffer, media_type="audio/mpeg", headers={"X-Text-Response": encoded_reply})

    except Exception as e:
        print(f"❌ [{bot_type}] Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "bots": list(BOT_CONFIG.keys()), "voices": list(VOICE_CONFIG.keys())}
