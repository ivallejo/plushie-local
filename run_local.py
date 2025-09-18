#!/usr/bin/env python3
"""
Script para ejecutar la API localmente con PostgreSQL
Requiere: Docker y docker-compose instalados
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_docker():
    """Verificar que Docker esté instalado y corriendo"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker no está instalado")
            return False

        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker no está corriendo")
            return False

        print("✅ Docker está instalado y corriendo")
        return True
    except FileNotFoundError:
        print("❌ Docker no está instalado")
        return False

def check_docker_compose():
    """Verificar que docker-compose esté disponible"""
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ docker-compose está disponible")
            return True
        else:
            # Intentar con docker compose (nueva sintaxis)
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ docker compose está disponible")
                return True
            else:
                print("❌ docker-compose no está disponible")
                return False
    except FileNotFoundError:
        print("❌ docker-compose no está disponible")
        return False

def start_postgres():
    """Iniciar PostgreSQL con Docker"""
    print("🐘 Iniciando PostgreSQL con Docker...")

    try:
        # Usar docker compose (nueva sintaxis)
        result = subprocess.run(['docker', 'compose', 'up', '-d'], cwd='.')
        if result.returncode != 0:
            # Intentar con docker-compose (vieja sintaxis)
            result = subprocess.run(['docker-compose', 'up', '-d'], cwd='.')

        if result.returncode == 0:
            print("✅ PostgreSQL iniciado correctamente")
            print("📍 PostgreSQL: localhost:5432")
            print("📍 PgAdmin: http://localhost:8080")
            print("   Usuario: admin@aiassistant.com")
            print("   Password: admin123")
            return True
        else:
            print("❌ Error al iniciar PostgreSQL")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def wait_for_postgres():
    """Esperar a que PostgreSQL esté listo"""
    print("⏳ Esperando a que PostgreSQL esté listo...")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        try:
            result = subprocess.run([
                'docker', 'exec', 'ai_assistant_postgres',
                'pg_isready', '-U', 'postgres'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ PostgreSQL está listo!")
                return True

        except Exception:
            pass

        attempt += 1
        time.sleep(2)
        print(f"   Intento {attempt}/{max_attempts}...")

    print("❌ PostgreSQL no respondió después de 60 segundos")
    return False

def init_database():
    """Inicializar la base de datos"""
    print("🗄️ Inicializando base de datos...")

    # Configurar variables de entorno para desarrollo local
    env_file = Path('.env.local')
    if env_file.exists():
        print("📄 Cargando configuración de .env.local")
        # Cargar variables de entorno desde .env.local
        import dotenv
        dotenv.load_dotenv('.env.local')

    # Ejecutar script de inicialización
    try:
        result = subprocess.run([sys.executable, 'init_db.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Base de datos inicializada correctamente")
            print(result.stdout)
            return True
        else:
            print("❌ Error inicializando base de datos")
            print("Error:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error ejecutando init_db.py: {e}")
        return False

def start_api():
    """Iniciar la API"""
    print("🚀 Iniciando AI Assistant API...")
    print("📍 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("")
    print("🎯 Endpoints disponibles:")
    print("   POST /users - Crear usuario")
    print("   POST /devices - Registrar dispositivo")
    print("   POST /process/{device_id} - Procesar audio")
    print("   GET / - Estado de la API")
    print("")
    print("🛑 Presiona Ctrl+C para detener")

    try:
        # Ejecutar la API
        os.environ['DATABASE_URL'] = 'postgresql://postgres:password123@localhost:5432/ai_assistant'
        subprocess.run([sys.executable, 'api/__init__.py'])
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo API...")
    except Exception as e:
        print(f"❌ Error iniciando API: {e}")

def cleanup():
    """Limpiar contenedores Docker"""
    print("🧹 Limpiando contenedores...")
    try:
        subprocess.run(['docker', 'compose', 'down'], cwd='.')
        print("✅ Contenedores detenidos")
    except Exception as e:
        print(f"⚠️ Error limpiando: {e}")

def main():
    """Función principal"""
    print("🚀 AI Assistant API - Desarrollo Local con PostgreSQL")
    print("=" * 60)

    # Verificar prerrequisitos
    if not check_docker():
        print("📦 Instala Docker desde: https://docker.com")
        return

    if not check_docker_compose():
        print("📦 Docker Compose está incluido con Docker Desktop")
        return

    # Iniciar PostgreSQL
    if not start_postgres():
        return

    # Esperar a que esté listo
    if not wait_for_postgres():
        cleanup()
        return

    # Inicializar base de datos
    if not init_database():
        cleanup()
        return

    print("")
    print("🎉 ¡Entorno de desarrollo listo!")
    print("📊 PostgreSQL: ✅ Conectado")
    print("🗄️ Base de datos: ✅ Inicializada")
    print("")

    # Iniciar API
    try:
        start_api()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()