import os
from gtts import gTTS
import io

def generate_test_audio(text: str, output_file: str = "test_audio.wav"):
    """Genera un archivo de audio usando gTTS (Google Text-to-Speech)"""
    tts = gTTS(text=text, lang='es')

    # Guardar directamente a archivo
    tts.save(output_file)
    print(f"Audio guardado en {output_file}")

def generate_test_audio_bytes(text: str):
    """Genera audio y devuelve bytes (como en api.py)"""
    tts = gTTS(text=text, lang='es')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    return audio_io.getvalue()

def test_api_with_generated_audio():
    """Genera audio de prueba, lo envía al API y guarda la respuesta"""
    import requests

    # Generar audio de entrada
    test_text = "¿como te llamas?"
    input_audio_file = "test_audio.wav"
    generate_test_audio(test_text, input_audio_file)

    # Enviar al API
    api_url = "http://localhost:8000/process/ESP32-PELUCHIN-1"
    with open(input_audio_file, "rb") as f:
        response = requests.post(api_url, data=f.read(), headers={"Content-Type": "application/octet-stream"})

    if response.status_code == 200:
        # Guardar respuesta
        output_file = "api_response.mp3"
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Respuesta del API guardada en {output_file}")
    else:
        print(f"Error en el API: {response.status_code}")

if __name__ == "__main__":
    # Texto de prueba
    # test_text = "Cuantos paises hay en el mundo?"
    # generate_test_audio(test_text)

    # Probar el API completo
    print("\nProbando el API completo...")
    test_api_with_generated_audio()