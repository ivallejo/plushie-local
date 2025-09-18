# 🗄️ Configuración de Base de Datos PostgreSQL

## 📋 REQUISITOS PREVIOS

```bash
# Instalar PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
# o
brew install postgresql  # macOS

# Instalar psycopg2 para Python
pip install psycopg2-binary
```

## 🏗️ CREACIÓN DE LA BASE DE DATOS

### **1. Crear Base de Datos**
```sql
-- Conectar como superusuario
sudo -u postgres psql

-- Crear usuario y base de datos
CREATE USER asistente_user WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE asistente_virtual OWNER asistente_user;
GRANT ALL PRIVILEGES ON DATABASE asistente_virtual TO asistente_user;

-- Salir
\q
```

### **2. Configurar Esquema**
```sql
-- Conectar a la base de datos
psql -U asistente_user -d asistente_virtual

-- Crear tablas
CREATE TABLE conversations (
    session_id VARCHAR(255) PRIMARY KEY,
    messages JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cache (
    id SERIAL PRIMARY KEY,
    input_hash VARCHAR(64) UNIQUE NOT NULL,
    input_text TEXT,
    output_data BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1
);

-- Crear índices para rendimiento
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);
CREATE INDEX idx_cache_hash ON cache USING HASH(input_hash);
CREATE INDEX idx_cache_accessed ON cache(last_accessed DESC);

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para conversations
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para cache
CREATE TRIGGER update_cache_last_accessed
    BEFORE UPDATE ON cache
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## 🔧 CONFIGURACIÓN EN PYTHON

### **Archivo: database.py**
```python
import os
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Conectar a PostgreSQL"""
        database_url = os.getenv("DATABASE_URL")

        if database_url:
            # Para producción (Heroku, etc.)
            url = urlparse(database_url)
            self.connection = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                user=url.username,
                password=url.password,
                database=url.path[1:],
                sslmode='require'
            )
        else:
            # Para desarrollo local
            self.connection = psycopg2.connect(
                host="localhost",
                port=5432,
                user="asistente_user",
                password="tu_password_seguro",
                database="asistente_virtual"
            )

        # Configurar para retornar diccionarios
        self.connection.autocommit = False

    def get_cursor(self):
        """Obtener cursor con soporte para dict"""
        return self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def save_conversation(self, session_id: str, messages: list):
        """Guardar conversación"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO conversations (session_id, messages)
                VALUES (%s, %s)
                ON CONFLICT (session_id)
                DO UPDATE SET messages = EXCLUDED.messages, updated_at = CURRENT_TIMESTAMP
            """, (session_id, psycopg2.extras.Json(messages)))
            self.connection.commit()

    def get_conversation(self, session_id: str):
        """Obtener conversación"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT messages FROM conversations WHERE session_id = %s
            """, (session_id,))
            result = cursor.fetchone()
            return result['messages'] if result else None

    def save_cache(self, input_text: str, output_data: bytes):
        """Guardar en caché"""
        import hashlib
        input_hash = hashlib.sha256(input_text.encode()).hexdigest()

        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO cache (input_hash, input_text, output_data)
                VALUES (%s, %s, %s)
                ON CONFLICT (input_hash)
                DO UPDATE SET
                    output_data = EXCLUDED.output_data,
                    last_accessed = CURRENT_TIMESTAMP,
                    access_count = cache.access_count + 1
            """, (input_hash, input_text, output_data))
            self.connection.commit()

    def get_cache(self, input_text: str):
        """Obtener de caché"""
        import hashlib
        input_hash = hashlib.sha256(input_text.encode()).hexdigest()

        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE cache
                SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                WHERE input_hash = %s
            """, (input_hash,))

            cursor.execute("""
                SELECT output_data FROM cache WHERE input_hash = %s
            """, (input_hash,))

            result = cursor.fetchone()
            if result:
                self.connection.commit()
                return result['output_data']
            else:
                self.connection.rollback()
                return None

    def cleanup_old_cache(self, days: int = 30):
        """Limpiar caché antiguo"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM cache
                WHERE last_accessed < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (days,))
            deleted_count = cursor.rowcount
            self.connection.commit()
            return deleted_count

    def get_stats(self):
        """Obtener estadísticas"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM conversations) as total_conversations,
                    (SELECT COUNT(*) FROM cache) as cache_entries,
                    (SELECT AVG(access_count) FROM cache) as avg_cache_access,
                    (SELECT pg_size_pretty(pg_database_size(current_database()))) as db_size
            """)
            return cursor.fetchone()

# Instancia global
db = DatabaseManager()
```

### **Archivo: api.py (Actualizado)**
```python
# Reemplazar la configuración de SQLite
from database import db

# En process_audio, reemplazar:
# cursor = conn.cursor()
# cursor.execute("SELECT output FROM cache WHERE input = ?", (texto,))
# cached = cursor.fetchone()

# Por:
cached = db.get_cache(texto)

# Y para guardar:
# cursor.execute("INSERT OR REPLACE INTO cache (input, output) VALUES (?, ?)", (texto, audio_out))
# conn.commit()

# Por:
db.save_cache(texto, audio_out)

# Para conversaciones:
# conversation_history = json.loads(result[0]) si result else [...]
db_conversation = db.get_conversation(session_id)
conversation_history = db_conversation if db_conversation else [...]

# Y guardar:
db.save_conversation(session_id, conversation_history)
```

## 📊 MIGRACIÓN DESDE SQLITE

### **Script de Migración**
```python
import sqlite3
import psycopg2
from database import db

def migrate_from_sqlite():
    """Migrar datos desde SQLite a PostgreSQL"""

    # Conectar a SQLite
    sqlite_conn = sqlite3.connect("cache.db")
    sqlite_cursor = sqlite_conn.cursor()

    print("🔄 Iniciando migración...")

    # Migrar conversaciones
    sqlite_cursor.execute("SELECT session_id, messages FROM conversations")
    conversations = sqlite_cursor.fetchall()

    for session_id, messages_json in conversations:
        try:
            import json
            messages = json.loads(messages_json)
            db.save_conversation(session_id, messages)
            print(f"✅ Migrada conversación: {session_id}")
        except Exception as e:
            print(f"❌ Error migrando conversación {session_id}: {e}")

    # Migrar caché
    sqlite_cursor.execute("SELECT input, output FROM cache")
    cache_entries = sqlite_cursor.fetchall()

    for input_text, output_data in cache_entries:
        try:
            db.save_cache(input_text, output_data)
            print(f"✅ Migrada entrada de caché: {input_text[:50]}...")
        except Exception as e:
            print(f"❌ Error migrando caché: {e}")

    sqlite_conn.close()
    print("🎉 Migración completada!")

if __name__ == "__main__":
    migrate_from_sqlite()
```

## 📈 OPTIMIZACIONES DE RENDIMIENTO

### **Configuración de PostgreSQL**
```sql
-- Configuración en postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### **Monitoreo**
```sql
-- Consultas útiles para monitoreo
SELECT * FROM pg_stat_activity;
SELECT * FROM pg_stat_user_tables;
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables;

-- Tamaño de tablas
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔧 MANTENIMIENTO

### **Backup Automático**
```bash
# Script de backup diario
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U asistente_user -h localhost asistente_virtual > backup_$DATE.sql

# Comprimir
gzip backup_$DATE.sql

# Mantener solo últimos 7 días
find . -name "backup_*.sql.gz" -mtime +7 -delete
```

### **Limpieza Programada**
```python
# Ejecutar diariamente
deleted = db.cleanup_old_cache(days=30)
print(f"🧹 Limpiados {deleted} entradas de caché antiguas")
```

---

**🚀 Con PostgreSQL tendrás:**
- ✅ Escalabilidad horizontal
- ✅ Alto rendimiento concurrente
- ✅ Backup y recuperación robustos
- ✅ Monitoreo avanzado
- ✅ JSON nativo para conversaciones