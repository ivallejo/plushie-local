from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from fastapi import Body
import whisper
from gtts import gTTS
import sqlite3
import os
from openai import AsyncOpenAI
import numpy as np
import soundfile as sf
import io
import asyncio
import ssl
import time
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Deshabilitar verificación SSL para desarrollo (no recomendado para producción)
ssl._create_default_https_context = ssl._create_unverified_context

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

app = FastAPI()

# Configurar modelos
model_stt = whisper.load_model("tiny")
# TTS con gTTS (Google Text-to-Speech)

# Configurar base de datos
conn = sqlite3.connect("cache.db")

# Función para migrar tabla de conversaciones
def migrate_conversations_table():
    cursor = conn.cursor()

    # Verificar si la tabla conversations tiene las columnas nuevas
    cursor.execute("PRAGMA table_info(conversations)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'device_id' not in column_names or 'user_id' not in column_names:
        print("Migrando tabla conversations...")

        # Crear tabla temporal con estructura nueva
        cursor.execute("""
        CREATE TABLE conversations_new (
            session_id TEXT PRIMARY KEY,
            device_id TEXT,
            user_id INTEGER,
            messages TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Copiar datos existentes
        cursor.execute("""
        INSERT INTO conversations_new (session_id, messages, updated_at)
        SELECT session_id, messages, updated_at FROM conversations
        """)

        # Reemplazar tabla antigua
        cursor.execute("DROP TABLE conversations")
        cursor.execute("ALTER TABLE conversations_new RENAME TO conversations")

        print("Tabla conversations migrada exitosamente")

    conn.commit()

# Función para migrar tabla de usuarios
def migrate_users_table():
    cursor = conn.cursor()

    # Verificar si la tabla users tiene las columnas nuevas
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    needs_migration = False
    if 'custom_prompt' not in column_names:
        needs_migration = True
    if 'ai_alias' not in column_names:
        needs_migration = True

    if needs_migration:
        print("Migrando tabla users...")

        # Crear tabla temporal con estructura nueva
        cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            preferences TEXT,
            custom_prompt TEXT,
            ai_alias TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Copiar datos existentes
        select_columns = []
        insert_columns = []

        if 'id' in column_names:
            select_columns.append('id')
            insert_columns.append('id')
        if 'name' in column_names:
            select_columns.append('name')
            insert_columns.append('name')
        if 'email' in column_names:
            select_columns.append('email')
            insert_columns.append('email')
        if 'phone' in column_names:
            select_columns.append('phone')
            insert_columns.append('phone')
        if 'preferences' in column_names:
            select_columns.append('preferences')
            insert_columns.append('preferences')
        if 'created_at' in column_names:
            select_columns.append('created_at')
            insert_columns.append('created_at')
        if 'updated_at' in column_names:
            select_columns.append('updated_at')
            insert_columns.append('updated_at')

        select_clause = ', '.join(select_columns)
        insert_clause = ', '.join(insert_columns)

        cursor.execute(f"""
        INSERT INTO users_new ({insert_clause})
        SELECT {select_clause} FROM users
        """)

        # Reemplazar tabla antigua
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        print("Tabla users migrada exitosamente")

    conn.commit()

# Crear tablas
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    preferences TEXT,  -- JSON con preferencias del usuario
    custom_prompt TEXT,  -- Prompt personalizado del usuario
    ai_alias TEXT,  -- Alias/nombre personalizado de la IA
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    user_id INTEGER,
    device_name TEXT,
    device_type TEXT,  -- ESP32, mobile, web, etc.
    location TEXT,     -- habitación, cocina, sala, etc.
    mac_address TEXT,
    ip_address TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# Crear tabla de conversaciones básica primero
conn.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT PRIMARY KEY,
    messages TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Migrar tablas si es necesario
migrate_conversations_table()
migrate_users_table()

# Tabla de caché
conn.execute("""
CREATE TABLE IF NOT EXISTS cache (input TEXT PRIMARY KEY, output BLOB)
""")

conn.commit()

# Configurar OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = os.getenv("ASSISTANT_ID")

# Funciones helper para usuarios y dispositivos
def create_user(name: str, email: Optional[str] = None, phone: Optional[str] = None, preferences: Optional[Dict[str, Any]] = None, custom_prompt: Optional[str] = None, ai_alias: Optional[str] = None):
    """Crear un nuevo usuario"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, email, phone, preferences, custom_prompt, ai_alias)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, phone, json.dumps(preferences) if preferences else None, custom_prompt, ai_alias))
    conn.commit()
    return cursor.lastrowid

def get_user(user_id: int):
    """Obtener información de un usuario"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return {
            "id": result[0],
            "name": result[1],
            "email": result[2],
            "phone": result[3],
            "preferences": json.loads(result[4]) if result[4] else None,
            "custom_prompt": result[5],
            "ai_alias": result[6],
            "created_at": result[7],
            "updated_at": result[8]
        }
    return None

def register_device(device_id: str, device_name: str, device_type: str = "ESP32",
                   location: Optional[str] = None, mac_address: Optional[str] = None,
                   user_id: Optional[int] = None):
    """Registrar un nuevo dispositivo"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO devices (device_id, user_id, device_name, device_type, location, mac_address, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (device_id, user_id, device_name, device_type, location, mac_address))
    conn.commit()

def get_device_info(device_id: str):
    """Obtener información de un dispositivo y su usuario"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, u.name as user_name, u.email, u.phone, u.preferences, u.custom_prompt, u.ai_alias
        FROM devices d
        LEFT JOIN users u ON d.user_id = u.id
        WHERE d.device_id = ?
    """, (device_id,))
    result = cursor.fetchone()
    if result:
        return {
            "device_id": result[0],
            "user_id": result[1],
            "device_name": result[2],
            "device_type": result[3],
            "location": result[4],
            "mac_address": result[5],
            "ip_address": result[6],
            "is_active": bool(result[7]),
            "last_seen": result[8],
            "created_at": result[9],
            "user_name": result[10],
            "user_email": result[11],
            "user_phone": result[12],
            "user_preferences": json.loads(result[13]) if result[13] else None,
            "user_custom_prompt": result[14],
            "user_ai_alias": result[15]
        }
    return None

def update_device_last_seen(device_id: str):
    """Actualizar último visto del dispositivo"""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE device_id = ?
    """, (device_id,))
    conn.commit()

async def process_audio(audio_data: bytes, session_id: str = "default_session"):
    start_time = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Iniciando procesamiento...")

    try:
        # Timeout general de 15 segundos
        result = await asyncio.wait_for(_process_audio_internal(audio_data, start_time, session_id), timeout=15.0)
        return result
    except asyncio.TimeoutError:
        print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - ERROR: Timeout de 15 segundos excedido")
        # Retornar respuesta de error
        error_response = "Lo siento, la respuesta está tardando demasiado. Inténtalo de nuevo."
        tts = gTTS(text=error_response, lang='es')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        return audio_io.getvalue()

async def _process_audio_internal(audio_data: bytes, start_time: float, session_id: str):
    # STT
    stt_start = time.time()
    audio_io = io.BytesIO(audio_data)
    audio, sr = sf.read(audio_io)
    audio = np.array(audio, dtype=np.float32)
    result = model_stt.transcribe(audio, language="es")
    texto = result["text"]
    stt_time = time.time() - stt_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - STT: '{texto}' ({stt_time:.2f}s)")

    # Caché por sesión
    cache_start = time.time()
    cursor = conn.cursor()
    cache_key = f"{session_id}:{texto}"
    cursor.execute("SELECT output FROM cache WHERE input = ?", (cache_key,))
    cached = cursor.fetchone()
    cache_time = time.time() - cache_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Caché: {cache_time:.4f}s")

    if cached:
        print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Respuesta desde caché")
        return cached[0]

    # LLM con OpenAI Chat Completions (con historial por sesión)
    llm_start = time.time()

    # Obtener información del dispositivo y usuario
    device_info = get_device_info(session_id)
    print(f"[{time.strftime('%H:%M:%S')}] device_info: {device_info} - Respuesta desde caché")

    # Obtener historial de conversación de la sesión
    cursor.execute("SELECT messages FROM conversations WHERE session_id = ?", (session_id,))
    result = cursor.fetchone()

    # Crear system prompt personalizado con información del usuario (SIEMPRE actualizar)
    user_name = device_info["user_name"] if device_info and device_info["user_name"] else "usuario"
    location = device_info["location"] if device_info and device_info["location"] else "esta ubicación"
    device_name = device_info["device_name"] if device_info and device_info["device_name"] else session_id
    ai_alias = device_info["user_ai_alias"] if device_info and device_info["user_ai_alias"] else "Asistente"

    # Usar custom_prompt del usuario si existe, sino usar el predeterminado
    if device_info and device_info["user_custom_prompt"]:
        # Reemplazar placeholders en el custom_prompt
        custom_prompt = device_info["user_custom_prompt"]
        custom_prompt = custom_prompt.replace("{user_name}", user_name)
        custom_prompt = custom_prompt.replace("{location}", location)
        custom_prompt = custom_prompt.replace("{device_name}", device_name)
        custom_prompt = custom_prompt.replace("{ai_alias}", ai_alias)
        system_prompt = custom_prompt
    else:
        # System prompt predeterminado con alias personalizado
        system_prompt = f"""Eres {ai_alias}, un asistente virtual personal para {user_name}.
        Estás ubicado en {location} y eres el dispositivo llamado {device_name}.
        Responde de manera clara, directa y útil en español.
        Dirígete a {user_name} de manera personal y natural.
        Evita explicaciones largas y ve al grano.
        Si conoces información personal de {user_name}, úsala para hacer respuestas más relevantes."""

    if result:
        conversation_history = json.loads(result[0])
        # SIEMPRE actualizar el system prompt con la información más reciente
        if conversation_history and conversation_history[0]["role"] == "system":
            conversation_history[0] = {"role": "system", "content": system_prompt}
        else:
            # Si no hay system prompt, agregarlo al inicio
            conversation_history.insert(0, {"role": "system", "content": system_prompt})
    else:
        conversation_history = [{"role": "system", "content": system_prompt}]

    # Agregar mensaje del usuario
    conversation_history.append({"role": "user", "content": texto})

    # Mantener solo los últimos 20 mensajes para no exceder límites
    if len(conversation_history) > 21:  # 1 system + 20 mensajes
        conversation_history = [conversation_history[0]] + conversation_history[-20:]

    # Llamar a Chat Completions con parámetros optimizados
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=100,  # Reducido para respuestas más concisas
        temperature=0.3,  # Más consistente y directo
        timeout=10.0  # Timeout de 10 segundos para la API
    )

    respuesta = response.choices[0].message.content

    # Agregar respuesta al historial
    conversation_history.append({"role": "assistant", "content": respuesta})

    # Guardar historial actualizado de la sesión
    user_id = device_info["user_id"] if device_info else None
    device_id = session_id  # El session_id es el device_id

    # Verificar si la tabla tiene las columnas nuevas
    cursor.execute("PRAGMA table_info(conversations)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'device_id' in column_names and 'user_id' in column_names:
        # Usar estructura nueva
        cursor.execute("""
            INSERT OR REPLACE INTO conversations (session_id, device_id, user_id, messages, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (session_id, device_id, user_id, json.dumps(conversation_history)))
    else:
        # Usar estructura antigua
        cursor.execute("""
            INSERT OR REPLACE INTO conversations (session_id, messages, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (session_id, json.dumps(conversation_history)))

    conn.commit()

    llm_time = time.time() - llm_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - LLM: '{respuesta}' ({llm_time:.2f}s)")
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Mensajes: {len(conversation_history)}")

    # TTS con gTTS
    tts_start = time.time()
    tts = gTTS(text=respuesta, lang='es')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    audio_out = audio_io.getvalue()
    tts_time = time.time() - tts_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - TTS: {len(audio_out)} bytes ({tts_time:.2f}s)")

    # Guardar en caché con session_id
    cache_save_start = time.time()
    cursor.execute("INSERT OR REPLACE INTO cache (input, output) VALUES (?, ?)", (cache_key, audio_out))
    conn.commit()
    cache_save_time = time.time() - cache_save_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Caché guardado: {cache_save_time:.4f}s")

    total_time = time.time() - start_time
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Total: {total_time:.2f}s")

    return audio_out

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

        # Obtener el usuario creado
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
        # Verificar que el usuario existe si se proporciona user_id
        if device.user_id:
            user = get_user(device.user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

        register_device(
            device_id=device.device_id,
            device_name=device.device_name,
            device_type=device.device_type,
            location=device.location,
            mac_address=device.mac_address,
            user_id=device.user_id
        )

        # Obtener información del dispositivo registrado
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

@app.put("/users/{user_id}/custom-prompt")
async def update_user_custom_prompt(user_id: int, custom_prompt: str):
    """Actualizar el prompt personalizado de un usuario"""
    try:
        # Verificar que el usuario existe
        user = get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Actualizar el custom_prompt
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET custom_prompt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (custom_prompt, user_id))
        conn.commit()

        return {
            "message": f"Prompt personalizado actualizado para usuario {user_id}",
            "custom_prompt": custom_prompt
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar prompt: {str(e)}")

@app.put("/users/{user_id}/ai-alias")
async def update_user_ai_alias(user_id: int, request: Request):
    """Actualizar el alias de la IA para un usuario"""
    try:
        # Verificar que el usuario existe
        user = get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Obtener el ai_alias del body
        body = await request.json()
        ai_alias = body.get("ai_alias")

        if not ai_alias:
            raise HTTPException(status_code=400, detail="ai_alias es requerido")

        # Actualizar el ai_alias
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET ai_alias = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ai_alias, user_id))
        conn.commit()

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
    # Actualizar último visto del dispositivo
    update_device_last_seen(session_id)

    audio = await request.body()
    return Response(content=await process_audio(audio, session_id), media_type="audio/mp3")

@app.post("/process")
async def process_legacy(request: Request):
    """Endpoint legacy para compatibilidad"""
    audio = await request.body()
    return Response(content=await process_audio(audio, "default_session"), media_type="audio/mp3")

@app.get("/stats/sessions")
async def get_session_stats():
    """Obtener estadísticas de sesiones activas"""
    cursor = conn.cursor()

    try:
        # Estadísticas generales
        cursor.execute("""
            SELECT
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(*) as total_conversations,
                AVG(LENGTH(messages)) as avg_conversation_size,
                MAX(updated_at) as last_activity
            FROM conversations
        """)

        stats = cursor.fetchone()

        # Sesiones activas (últimas 24 horas)
        cursor.execute("""
            SELECT session_id, updated_at, LENGTH(messages) as conversation_size
            FROM conversations
            WHERE updated_at > datetime('now', '-1 day')
            ORDER BY updated_at DESC
            LIMIT 10
        """)

        active_sessions = cursor.fetchall()

        return {
            "total_sessions": stats[0] or 0,
            "total_conversations": stats[1] or 0,
            "avg_conversation_size": float(stats[2]) if stats[2] else 0,
            "last_activity": stats[3],
            "active_sessions": [
                {
                    "session_id": session[0],
                    "last_activity": session[1],
                    "conversation_size": session[2]
                } for session in active_sessions
            ]
        }

    except Exception as e:
        return {"error": f"Error obteniendo estadísticas: {str(e)}"}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Eliminar una sesión específica"""
    cursor = conn.cursor()

    try:
        # Eliminar conversación
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        conversations_deleted = cursor.rowcount

        # Eliminar caché de la sesión
        cache_key_pattern = f"{session_id}:%"
        cursor.execute("DELETE FROM cache WHERE input LIKE ?", (cache_key_pattern,))
        cache_deleted = cursor.rowcount

        conn.commit()

        return {
            "message": f"Sesión {session_id} eliminada",
            "conversations_deleted": conversations_deleted,
            "cache_deleted": cache_deleted
        }

    except Exception as e:
        conn.rollback()
        return {"error": f"Error eliminando sesión: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)