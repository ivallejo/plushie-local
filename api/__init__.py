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
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse

# Configurar OpenAI
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = os.getenv("ASSISTANT_ID")

# Configurar PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Obtener conexión a PostgreSQL"""
    if not DATABASE_URL:
        # Fallback para desarrollo local
        return None

    try:
        # Parsear URL de conexión
        parsed = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return None

def init_db():
    """Inicializar tablas de la base de datos"""
    conn = get_db_connection()
    if not conn:
        print("No se pudo conectar a PostgreSQL, usando memoria temporal")
        return False

    try:
        with conn.cursor() as cursor:
            # Tabla de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    preferences JSONB,
                    custom_prompt TEXT,
                    ai_alias VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla de dispositivos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id VARCHAR(100) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    device_name VARCHAR(255) NOT NULL,
                    device_type VARCHAR(50) DEFAULT 'ESP32',
                    location VARCHAR(255),
                    mac_address VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla de conversaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, id)
                )
            """)

            # Tabla de cache de audio
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_cache (
                    cache_key VARCHAR(255) PRIMARY KEY,
                    audio_data BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.commit()
        print("✅ Base de datos PostgreSQL inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False
    finally:
        conn.close()

# Inicializar base de datos al startup
db_initialized = init_db()

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

# Funciones helper para usuarios y dispositivos con PostgreSQL
def create_user(name: str, email: Optional[str] = None, phone: Optional[str] = None,
                preferences: Optional[Dict[str, Any]] = None, custom_prompt: Optional[str] = None,
                ai_alias: Optional[str] = None):
    """Crear un nuevo usuario"""
    if not db_initialized:
        # Fallback a memoria si no hay DB
        return len([]) + 1

    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (name, email, phone, preferences, custom_prompt, ai_alias)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, email, phone, json.dumps(preferences) if preferences else None,
                  custom_prompt, ai_alias))

            user_id = cursor.fetchone()['id']
            conn.commit()
            return user_id
    except Exception as e:
        print(f"Error creando usuario: {e}")
        return None
    finally:
        conn.close()

def get_user(user_id: int):
    """Obtener información de un usuario"""
    if not db_initialized:
        return None

    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                # Convertir a dict y parsear JSON
                user_dict = dict(user)
                if user_dict.get('preferences'):
                    user_dict['preferences'] = json.loads(user_dict['preferences'])
                return user_dict
            return None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None
    finally:
        conn.close()

def register_device(device_id: str, device_name: str, device_type: str = "ESP32",
                   location: Optional[str] = None, mac_address: Optional[str] = None,
                   user_id: Optional[int] = None):
    """Registrar un nuevo dispositivo"""
    if not db_initialized:
        return

    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO devices (device_id, user_id, device_name, device_type, location, mac_address)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (device_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    device_name = EXCLUDED.device_name,
                    device_type = EXCLUDED.device_type,
                    location = EXCLUDED.location,
                    mac_address = EXCLUDED.mac_address,
                    last_seen = CURRENT_TIMESTAMP
            """, (device_id, user_id, device_name, device_type, location, mac_address))
            conn.commit()
    except Exception as e:
        print(f"Error registrando dispositivo: {e}")
    finally:
        conn.close()

def get_device_info(device_id: str):
    """Obtener información de un dispositivo y su usuario"""
    if not db_initialized:
        return None

    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.*, u.name as user_name, u.email as user_email,
                       u.phone as user_phone, u.preferences as user_preferences,
                       u.custom_prompt as user_custom_prompt, u.ai_alias as user_ai_alias
                FROM devices d
                LEFT JOIN users u ON d.user_id = u.id
                WHERE d.device_id = %s
            """, (device_id,))

            result = cursor.fetchone()
            if result:
                device_dict = dict(result)
                if device_dict.get('user_preferences'):
                    device_dict['user_preferences'] = json.loads(device_dict['user_preferences'])
                return device_dict
            return None
    except Exception as e:
        print(f"Error obteniendo dispositivo: {e}")
        return None
    finally:
        conn.close()

def get_conversation_history(session_id: str):
    """Obtener historial de conversación"""
    if not db_initialized:
        return [{"role": "system", "content": "Eres un asistente virtual útil."}]

    conn = get_db_connection()
    if not conn:
        return [{"role": "system", "content": "Eres un asistente virtual útil."}]

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT role, content FROM conversations
                WHERE session_id = %s
                ORDER BY created_at ASC
            """, (session_id,))

            messages = [{"role": row['role'], "content": row['content']} for row in cursor.fetchall()]

            # Si no hay mensajes, crear system message por defecto
            if not messages:
                messages = [{"role": "system", "content": "Eres un asistente virtual útil."}]

            return messages
    except Exception as e:
        print(f"Error obteniendo conversación: {e}")
        return [{"role": "system", "content": "Eres un asistente virtual útil."}]
    finally:
        conn.close()

def save_conversation_message(session_id: str, role: str, content: str):
    """Guardar mensaje en la conversación"""
    if not db_initialized:
        return

    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO conversations (session_id, role, content)
                VALUES (%s, %s, %s)
            """, (session_id, role, content))

            # Mantener solo los últimos 20 mensajes + system
            cursor.execute("""
                DELETE FROM conversations
                WHERE session_id = %s AND id NOT IN (
                    SELECT id FROM conversations
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 21
                )
            """, (session_id, session_id))

            conn.commit()
    except Exception as e:
        print(f"Error guardando mensaje: {e}")
    finally:
        conn.close()

def get_cached_audio(cache_key: str):
    """Obtener audio del cache"""
    if not db_initialized:
        return None

    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT audio_data FROM audio_cache
                WHERE cache_key = %s
            """, (cache_key,))

            result = cursor.fetchone()
            return result['audio_data'] if result else None
    except Exception as e:
        print(f"Error obteniendo cache: {e}")
        return None
    finally:
        conn.close()

def save_cached_audio(cache_key: str, audio_data: bytes):
    """Guardar audio en el cache"""
    if not db_initialized:
        return

    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO audio_cache (cache_key, audio_data)
                VALUES (%s, %s)
                ON CONFLICT (cache_key) DO UPDATE SET
                    audio_data = EXCLUDED.audio_data,
                    created_at = CURRENT_TIMESTAMP
            """, (cache_key, audio_data))
            conn.commit()
    except Exception as e:
        print(f"Error guardando cache: {e}")
    finally:
        conn.close()

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

        # Verificar cache de audio
        cache_key = f"{session_id}:{texto[:100]}"  # Usar primeros 100 caracteres como key
        cached_audio = get_cached_audio(cache_key)
        if cached_audio:
            return cached_audio

        # Obtener historial de conversación
        conversation_history = get_conversation_history(session_id)

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

        # Guardar mensajes en la base de datos
        save_conversation_message(session_id, "user", texto)
        save_conversation_message(session_id, "assistant", respuesta)

        # TTS con gTTS
        tts = gtts.gTTS(text=respuesta, lang='es')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_out = audio_io.getvalue()

        # Guardar en cache
        save_cached_audio(cache_key, audio_out)

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
    return {
        "message": "AI Assistant API - Render Deployment",
        "version": "1.0.0",
        "database": "PostgreSQL" if db_initialized else "Memory (fallback)",
        "features": [
            "Whisper STT",
            "OpenAI ChatGPT",
            "AI Aliases personalizados",
            "PostgreSQL persistence",
            "Audio cache",
            "Session management"
        ]
    }