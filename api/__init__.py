from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from fastapi import Body
import openai
import gtts
import io
import asyncio
import json
from typing import Optional, Dict, Any
import os
import whisper
import numpy as np
import soundfile as sf

# Configurar OpenAI
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = os.getenv("ASSISTANT_ID")

# Modelos Pydantic para requests
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    custom_prompt: Optional[str] = None
    ai_alias: Optional[str] = None

class DeviceRegister(BaseModel):
    device_id: str
    device_name: str
    device_type: str = "ESP32"
    location: Optional[str] = None
    mac_address: Optional[str] = None
    user_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    preferences: Optional[Dict[str, Any]]
    custom_prompt: Optional[str]
    ai_alias: Optional[str]
    created_at: str

class DeviceResponse(BaseModel):
    device_id: str
    user_id: Optional[int]
    device_name: str
    device_type: str
    location: Optional[str]
    mac_address: Optional[str]
    is_active: bool
    last_seen: str
    created_at: str

class AIAliasUpdate(BaseModel):
    ai_alias: str

# Almacenamiento en memoria para Vercel (no persistente)
users_db = {}
devices_db = {}
conversations_db = {}
cache_db = {}

# Funciones helper para usuarios y dispositivos
def create_user(name: str, email: Optional[str] = None, phone: Optional[str] = None, preferences: Optional[Dict[str, Any]] = None, custom_prompt: Optional[str] = None, ai_alias: Optional[str] = None):
    """Crear un nuevo usuario"""
    user_id = len(users_db) + 1
    users_db[user_id] = {
        "id": user_id,
        "name": name,
        "email": email,
        "phone": phone,
        "preferences": preferences,
        "custom_prompt": custom_prompt,
        "ai_alias": ai_alias,
        "created_at": "2025-09-18T06:28:00Z",
        "updated_at": "2025-09-18T06:28:00Z"
    }
    return user_id

def get_user(user_id: int):
    """Obtener información de un usuario"""
    return users_db.get(user_id)

def register_device(device_id: str, device_name: str, device_type: str = "ESP32",
                   location: Optional[str] = None, mac_address: Optional[str] = None,
                   user_id: Optional[int] = None):
    """Registrar un nuevo dispositivo"""
    devices_db[device_id] = {
        "device_id": device_id,
        "user_id": user_id,
        "device_name": device_name,
        "device_type": device_type,
        "location": location,
        "mac_address": mac_address,
        "is_active": True,
        "last_seen": "2025-09-18T06:28:00Z",
        "created_at": "2025-09-18T06:28:00Z"
    }

def get_device_info(device_id: str):
    """Obtener información de un dispositivo y su usuario"""
    device = devices_db.get(device_id)
    if device and device["user_id"]:
        user = get_user(device["user_id"])
        if user:
            return {
                **device,
                "user_name": user["name"],
                "user_email": user["email"],
                "user_phone": user["phone"],
                "user_preferences": user["preferences"],
                "user_custom_prompt": user["custom_prompt"],
                "user_ai_alias": user["ai_alias"]
            }
    return device

async def process_audio(audio_data: bytes, session_id: str = "default_session"):
    """Procesar audio con Whisper y OpenAI"""
    try:
        # STT con Whisper
        audio_io = io.BytesIO(audio_data)
        audio, sr = sf.read(audio_io)
        audio = np.array(audio, dtype=np.float32)

        # Cargar modelo Whisper (se cachea automáticamente)
        model = whisper.load_model("tiny")
        result = model.transcribe(audio, language="es")
        texto = result["text"]

        # Obtener información del dispositivo y usuario
        device_info = get_device_info(session_id)

        # Crear system prompt personalizado
        user_name = device_info.get("user_name", "usuario") if device_info else "usuario"
        location = device_info.get("location", "esta ubicación") if device_info else "esta ubicación"
        device_name = device_info.get("device_name", session_id) if device_info else session_id
        ai_alias = device_info.get("user_ai_alias", "Asistente") if device_info else "Asistente"

        # Usar custom_prompt del usuario si existe
        if device_info and device_info.get("user_custom_prompt"):
            custom_prompt = device_info["user_custom_prompt"]
            custom_prompt = custom_prompt.replace("{user_name}", user_name)
            custom_prompt = custom_prompt.replace("{location}", location)
            custom_prompt = custom_prompt.replace("{device_name}", device_name)
            custom_prompt = custom_prompt.replace("{ai_alias}", ai_alias)
            system_prompt = custom_prompt
        else:
            system_prompt = f"""Eres {ai_alias}, un asistente virtual personal para {user_name}.
            Estás ubicado en {location} y eres el dispositivo llamado {device_name}.
            Responde de manera clara, directa y útil en español."""

        # Obtener historial de conversación
        conversation_history = conversations_db.get(session_id, [{"role": "system", "content": system_prompt}])

        # Actualizar system prompt si es necesario
        if conversation_history and conversation_history[0]["role"] == "system":
            conversation_history[0] = {"role": "system", "content": system_prompt}

        # Agregar mensaje del usuario
        conversation_history.append({"role": "user", "content": texto})

        # Mantener solo los últimos mensajes
        if len(conversation_history) > 21:
            conversation_history = [conversation_history[0]] + conversation_history[-20:]

        # Llamar a OpenAI
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=100,
            temperature=0.3
        )

        respuesta = response.choices[0].message.content

        # Agregar respuesta al historial
        conversation_history.append({"role": "assistant", "content": respuesta})
        conversations_db[session_id] = conversation_history

        # TTS con gTTS
        tts = gtts.gTTS(text=respuesta, lang='es')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_out = audio_io.getvalue()

        return audio_out

    except Exception as e:
        # Respuesta de error
        error_response = "Lo siento, ha ocurrido un error. Inténtalo de nuevo."
        tts = gtts.gTTS(text=error_response, lang='es')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        return audio_io.getvalue()

# Crear aplicación FastAPI
app = FastAPI(title="AI Assistant API", version="1.0.0")

# Endpoints de registro de usuarios y dispositivos
@app.post("/users", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate):
    """Crear un nuevo usuario"""
    try:
        user_id = create_user(
            name=user.name,
            email=user.email,
            phone=user.phone,
            preferences=user.preferences,
            custom_prompt=user.custom_prompt,
            ai_alias=user.ai_alias
        )

        user_data = get_user(user_id)
        if not user_data:
            raise HTTPException(status_code=500, detail="Error al crear usuario")

        return UserResponse(**user_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")

@app.post("/devices", response_model=DeviceResponse)
async def register_device_endpoint(device: DeviceRegister):
    """Registrar un nuevo dispositivo"""
    try:
        if device.user_id and not get_user(device.user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        register_device(
            device_id=device.device_id,
            device_name=device.device_name,
            device_type=device.device_type,
            location=device.location,
            mac_address=device.mac_address,
            user_id=device.user_id
        )

        device_info = get_device_info(device.device_id)
        if not device_info:
            raise HTTPException(status_code=500, detail="Error al registrar dispositivo")

        return DeviceResponse(**device_info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar dispositivo: {str(e)}")

@app.get("/devices/{device_id}")
async def get_device_endpoint(device_id: str):
    """Obtener información de un dispositivo"""
    try:
        device_info = get_device_info(device_id)
        if not device_info:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

        return device_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener dispositivo: {str(e)}")

@app.put("/users/{user_id}/ai-alias")
async def update_user_ai_alias(user_id: int, request: Request):
    """Actualizar el alias de la IA para un usuario"""
    try:
        user = get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        body = await request.json()
        ai_alias = body.get("ai_alias")

        if not ai_alias:
            raise HTTPException(status_code=400, detail="ai_alias es requerido")

        user["ai_alias"] = ai_alias
        user["updated_at"] = "2025-09-18T06:28:00Z"

        return {
            "message": f"Alias de IA actualizado para usuario {user_id}",
            "ai_alias": ai_alias
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar alias: {str(e)}")

@app.get("/users/{user_id}")
async def get_user_endpoint(user_id: int):
    """Obtener información de un usuario"""
    try:
        user = get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")

@app.post("/process/{session_id}")
async def process_with_session(session_id: str, request: Request):
    """Endpoint con soporte de sesiones independientes"""
    audio = await request.body()
    return Response(content=await process_audio(audio, session_id), media_type="audio/mp3")

@app.post("/process")
async def process_legacy(request: Request):
    """Endpoint legacy para compatibilidad"""
    audio = await request.body()
    return Response(content=await process_audio(audio, "default_session"), media_type="audio/mp3")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "AI Assistant API - Vercel Deployment", "version": "1.0.0"}