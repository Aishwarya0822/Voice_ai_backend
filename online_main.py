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

# Bot configurations with Russian support
BOT_CONFIG = {
    "appointment": {
        "greeting": "Hi, this is the Healthcare Center. How can I help you?",
        "voice": "alloy",
        "handler": appointment_gpt
    },
    "appointment_ru": {
        "greeting": "Привет, это медицинский центр. Как я могу вам помочь?",
        "voice": "alloy",
        "handler": appointment_gpt_ru
    },
    "insurance": {
        "greeting": "Hello! This is the Insurance Assistance Center. How can I assist you?",
        "voice": "echo", 
        "handler": insurance_gpt
    },
    "insurance_ru": {
        "greeting": "Здравствуйте! Это центр страховой поддержки. Как я могу вам помочь?",
        "voice": "echo",
        "handler": insurance_gpt_ru
    }
}

async def speech_to_text(file_path: str, language: str = "en") -> str:
    """Async STT with language support"""
    loop = asyncio.get_event_loop()
    
    def _transcribe():
        mime_type = mimetypes.guess_type(file_path)[0] or "audio/mpeg"
        with open(file_path, "rb") as audio_file:
            return client.audio.transcriptions.create(
                model="whisper-1",
                file=(os.path.basename(file_path), audio_file, mime_type),
                language=language
            ).text
    
    return await loop.run_in_executor(executor, _transcribe)

async def text_to_speech(text: str, voice: str) -> io.BytesIO:
    """Async TTS with memory optimization"""
    loop = asyncio.get_event_loop()
    
    def _synthesize():
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text
        )
        return io.BytesIO(response.read())
    
    return await loop.run_in_executor(executor, _synthesize)

@app.get("/")
async def root():
    return {"message": "Voice AI API Ready ✅", "bots": list(BOT_CONFIG.keys())}

@app.get("/greeting/{bot_type}")
async def get_greeting(bot_type: str):
    """Single greeting endpoint with audio and text"""
    if bot_type not in BOT_CONFIG:
        return JSONResponse(
            content={"error": f"Invalid bot. Available: {list(BOT_CONFIG.keys())}"},
            status_code=400
        )
    
    config = BOT_CONFIG[bot_type]
    print(f"👋 [{bot_type}] Greeting: {config['greeting']}")
    
    # Generate audio
    audio_buffer = await text_to_speech(config["greeting"], config["voice"])
    audio_buffer.seek(0)
    
    # Encode text for header
    encoded_text = base64.b64encode(config["greeting"].encode('utf-8')).decode('ascii')
    
    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={"X-Text-Response": encoded_text}
    )

@app.post("/chat")
async def unified_chat(
    file: UploadFile = File(...),
    bot_type: str = Query(..., description="Bot type: appointment, appointment_ru, insurance, insurance_ru"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Unified chat endpoint with Russian support"""
    
    if bot_type not in BOT_CONFIG:
        return JSONResponse(
            content={"error": f"Invalid bot. Available: {list(BOT_CONFIG.keys())}"},
            status_code=400
        )
    
    try:
        config = BOT_CONFIG[bot_type]
        unique_id = uuid.uuid4().hex
        temp_audio = f"temp_{unique_id}_{bot_type}.wav"
        
        # Determine language for STT
        language = "ru" if "_ru" in bot_type else "en"
        
        # Save uploaded file
        content = await file.read()
        with open(temp_audio, "wb") as f:
            f.write(content)
        
        # STT with language detection
        user_text = await speech_to_text(temp_audio, language)
        user_text = user_text.strip() or "Silent audio detected"
        
        print(f"🧑 [{bot_type}] User: {user_text}")
        
        # Get bot response
        loop = asyncio.get_event_loop()
        bot_reply = await loop.run_in_executor(executor, config["handler"], user_text)
        
        print(f"🤖 [{bot_type}] Bot: {bot_reply}")
        
        # Generate audio response
        audio_buffer = await text_to_speech(bot_reply, config["voice"])
        
        print(f"📤 [{bot_type}] Response text: {bot_reply}")
        
        # Cleanup
        background_tasks.add_task(os.remove, temp_audio)
        
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"X-Text-Response": bot_reply}

        )
        
    except Exception as e:
        print(f"❌ [{bot_type}] Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "bots": list(BOT_CONFIG.keys())}