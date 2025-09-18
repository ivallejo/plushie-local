#!/usr/bin/env python3
"""
Script de prueba para la API desplegada en Vercel
"""

import requests
import json

# URL de tu API en Vercel (cambia esto por tu URL real)
VERCEL_URL = "https://tu-proyecto.vercel.app"

def test_create_user():
    """Prueba crear un usuario"""
    url = f"{VERCEL_URL}/users"
    data = {
        "name": "Test User",
        "email": "test@email.com",
        "ai_alias": "Test Assistant",
        "custom_prompt": "Eres {ai_alias}, un asistente de prueba para {user_name}."
    }

    print("🧪 Creando usuario...")
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Usuario creado: {user['name']} (ID: {user['id']})")
            return user['id']
        else:
            print(f"❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_register_device(user_id):
    """Prueba registrar un dispositivo"""
    url = f"{VERCEL_URL}/devices"
    data = {
        "device_id": "TEST-ESP32-001",
        "device_name": "ESP32 Test Device",
        "location": "Sala de pruebas",
        "user_id": user_id
    }

    print("📱 Registrando dispositivo...")
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            device = response.json()
            print(f"✅ Dispositivo registrado: {device['device_name']}")
            return device['device_id']
        else:
            print(f"❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_get_device(device_id):
    """Prueba obtener información del dispositivo"""
    url = f"{VERCEL_URL}/devices/{device_id}"

    print("📡 Obteniendo información del dispositivo...")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            device = response.json()
            print(f"✅ Dispositivo encontrado: {device['device_name']}")
            print(f"   Usuario: {device.get('user_name', 'N/A')}")
            print(f"   Alias IA: {device.get('user_ai_alias', 'N/A')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_update_ai_alias(user_id):
    """Prueba actualizar el alias de IA"""
    url = f"{VERCEL_URL}/users/{user_id}/ai-alias"
    data = {"ai_alias": "Super Assistant"}

    print("🎭 Actualizando alias de IA...")
    try:
        response = requests.put(url, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Alias actualizado: {result['ai_alias']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_process_audio(device_id):
    """Prueba procesar audio (con datos dummy)"""
    url = f"{VERCEL_URL}/process/{device_id}"

    # Crear datos de audio dummy (no realistas, solo para prueba)
    dummy_audio = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00"

    print("🎵 Probando procesamiento de audio...")
    try:
        response = requests.post(url, data=dummy_audio, headers={'Content-Type': 'application/octet-stream'})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Audio procesado correctamente ({len(response.content)} bytes)")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de la API en Vercel")
    print(f"📍 URL: {VERCEL_URL}")
    print("=" * 50)

    # Prueba 1: Crear usuario
    user_id = test_create_user()
    if not user_id:
        print("❌ No se pudo crear usuario. Abortando pruebas.")
        return

    print()

    # Prueba 2: Registrar dispositivo
    device_id = test_register_device(user_id)
    if not device_id:
        print("❌ No se pudo registrar dispositivo. Abortando pruebas.")
        return

    print()

    # Prueba 3: Obtener información del dispositivo
    if not test_get_device(device_id):
        print("❌ No se pudo obtener información del dispositivo.")
        return

    print()

    # Prueba 4: Actualizar alias de IA
    if not test_update_ai_alias(user_id):
        print("❌ No se pudo actualizar alias de IA.")
        return

    print()

    # Prueba 5: Procesar audio
    if not test_process_audio(device_id):
        print("❌ No se pudo procesar audio.")
        return

    print()
    print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    print("✅ Tu API está funcionando correctamente en Vercel")

if __name__ == "__main__":
    main()