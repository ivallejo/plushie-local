#!/usr/bin/env python3
"""
Script para probar la conexión a PostgreSQL
Ejecutar: python3 test_postgres_connection.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
from dotenv import load_dotenv

def test_connection():
    """Probar conexión a PostgreSQL"""
    # Cargar variables de entorno
    load_dotenv('.env.local')

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada en .env.local")
        print("Configura tu DATABASE_URL en el archivo .env.local")
        return False

    print(f"🔗 Intentando conectar a: {DATABASE_URL}")

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

        print("✅ Conexión a PostgreSQL exitosa!")

        # Probar consultas básicas
        with conn.cursor() as cursor:
            # Versión de PostgreSQL
            cursor.execute('SELECT version();')
            version = cursor.fetchone()
            print(f"📊 PostgreSQL versión: {version['version'][:50]}...")

            # Listar bases de datos
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = cursor.fetchall()
            print(f"🗄️ Bases de datos disponibles: {[db['datname'] for db in databases]}")

        conn.close()
        print("✅ Conexión cerrada correctamente")
        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verifica que PostgreSQL esté corriendo")
        print("2. Verifica las credenciales en DATABASE_URL")
        print("3. Verifica que el puerto esté abierto")
        print("4. Verifica que la base de datos exista")
        return False

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_database_setup():
    """Probar que las tablas estén creadas"""
    load_dotenv('.env.local')
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada")
        return False

    try:
        parsed = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            cursor_factory=RealDictCursor
        )

        with conn.cursor() as cursor:
            # Verificar tablas
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('users', 'devices', 'conversations', 'audio_cache')
            """)

            tables = cursor.fetchall()
            existing_tables = [table['table_name'] for table in tables]

            expected_tables = ['users', 'devices', 'conversations', 'audio_cache']
            missing_tables = [table for table in expected_tables if table not in existing_tables]

            if missing_tables:
                print(f"⚠️ Tablas faltantes: {missing_tables}")
                print("Ejecuta: python3 init_db.py")
                return False
            else:
                print("✅ Todas las tablas están creadas:")
                for table in existing_tables:
                    print(f"   - {table}")

                # Contar registros en cada tabla
                for table in expected_tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    print(f"   - {table}: {count} registros")

                return True

        conn.close()

    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando conexión a PostgreSQL...")
    print("=" * 50)

    # Probar conexión básica
    if test_connection():
        print("\n" + "=" * 50)
        print("📊 Verificando configuración de base de datos...")

        # Probar configuración de tablas
        test_database_setup()

        print("\n" + "=" * 50)
        print("🎉 ¡PostgreSQL está listo!")
        print("Puedes ejecutar: python3 api/__init__.py")
    else:
        print("\n" + "=" * 50)
        print("❌ Configura tu PostgreSQL y vuelve a ejecutar este script")