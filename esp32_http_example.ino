// ESP32 - Cliente HTTP para Asistente Virtual
// Requiere instalar: HTTPClient, WiFiClientSecure

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// Configuración WiFi
const char* ssid = "TU_WIFI_SSID";
const char* password = "TU_WIFI_PASSWORD";

// URL del servidor
const char* serverUrl = "http://192.168.1.100:8000/process"; // Cambia la IP

// Pines para I2S (ejemplo para INMP441)
#define I2S_WS 25
#define I2S_SD 33
#define I2S_SCK 32

void setup() {
    Serial.begin(115200);

    // Conectar WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando a WiFi...");
    }
    Serial.println("WiFi conectado");

    // Configurar I2S para micrófono
    setupMicrophone();
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        // Grabar audio por 3 segundos
        Serial.println("Grabando audio...");
        uint8_t* audioBuffer = recordAudio(3); // 3 segundos

        if (audioBuffer != nullptr) {
            // Enviar a API
            sendAudioToAPI(audioBuffer, 48000); // 48kHz * 3s * 2 bytes

            free(audioBuffer); // Liberar memoria
        }
    }

    delay(5000); // Esperar 5 segundos entre requests
}

void sendAudioToAPI(uint8_t* audioData, size_t dataSize) {
    HTTPClient http;

    Serial.println("Enviando audio a API...");

    // Configurar request
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/octet-stream");

    // Enviar datos de audio
    int httpResponseCode = http.POST(audioData, dataSize);

    if (httpResponseCode > 0) {
        Serial.printf("Respuesta HTTP: %d\n", httpResponseCode);

        // Obtener respuesta (audio)
        WiFiClient* stream = http.getStreamPtr();
        size_t responseSize = http.getSize();

        if (responseSize > 0) {
            Serial.printf("Recibido audio de %d bytes\n", responseSize);

            // Leer y reproducir respuesta
            uint8_t* responseBuffer = (uint8_t*)malloc(responseSize);
            if (responseBuffer) {
                size_t readBytes = stream->readBytes(responseBuffer, responseSize);
                Serial.printf("Leídos %d bytes de respuesta\n", readBytes);

                // Aquí iría el código para reproducir el audio MP3
                // (requiere librería adicional como ESP32-audioI2S)

                free(responseBuffer);
            }
        }
    } else {
        Serial.printf("Error HTTP: %d\n", httpResponseCode);
    }

    http.end();
}

uint8_t* recordAudio(int seconds) {
    // Configuración I2S básica (simplificada)
    // En un implementación real necesitarías configurar I2S correctamente

    size_t bufferSize = 48000 * seconds * 2; // 48kHz, 16-bit
    uint8_t* buffer = (uint8_t*)malloc(bufferSize);

    if (buffer == nullptr) {
        Serial.println("Error: No hay memoria suficiente");
        return nullptr;
    }

    // Aquí iría el código para leer del micrófono I2S
    // Por simplicidad, simulamos datos de audio
    for (size_t i = 0; i < bufferSize; i++) {
        buffer[i] = random(0, 255); // Datos simulados
    }

    Serial.printf("Audio grabado: %d bytes\n", bufferSize);
    return buffer;
}

void setupMicrophone() {
    // Configuración I2S para micrófono INMP441
    // Esto es solo un ejemplo básico

    Serial.println("Configurando micrófono...");
    // Configuración I2S real iría aquí
}