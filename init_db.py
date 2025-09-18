#!/usr/bin/env python3
"""
Script para inicializar la base de datos PostgreSQL
Ejecutar: python init_db.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse

def init_database():
    """Inicializar todas las tablas de la base de datos"""

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada")
        print("Configura la variable de entorno DATABASE_URL")
        return False

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

        print("✅ Conectado a PostgreSQL")

        with conn.cursor() as cursor:
            # Tabla de usuarios
            print("📝 Creando tabla users...")
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
            print("📝 Creando tabla devices...")
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
            print("📝 Creando tabla conversations...")
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
            print("📝 Creando tabla audio_cache...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_cache (
                    cache_key VARCHAR(255) PRIMARY KEY,
                    audio_data BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Crear índices para mejor rendimiento
            print("📝 Creando índices...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_cache_key ON audio_cache(cache_key)")

        conn.commit()
        print("✅ Base de datos inicializada correctamente")
        print("📊 Tablas creadas:")
        print("   - users")
        print("   - devices")
        print("   - conversations")
        print("   - audio_cache")
        print("   - índices de rendimiento")

        return True

    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Inicializando base de datos PostgreSQL...")
    success = init_database()

    if success:
        print("\n🎉 ¡Base de datos lista!")
        print("Tu AI Assistant API puede usar PostgreSQL para persistencia completa.")
    else:
        print("\n❌ Error en la inicialización.")
        print("Verifica tu configuración de DATABASE_URL.")