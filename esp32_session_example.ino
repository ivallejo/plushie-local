// ESP32 - Cliente con Sesiones Independientes
// Cada ESP32 tiene su propia conversación

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// Configuración WiFi
const char* ssid = "TU_WIFI_SSID";
const char* password = "TU_WIFI_PASSWORD";

// URL base del servidor
const char* serverUrl = "http://192.168.1.100:8000/process/";

// ID único del dispositivo (MAC Address)
String deviceId = "";

// Función para obtener ID único del dispositivo
String getDeviceId() {
    if (deviceId == "") {
        // Usar MAC Address como ID único
        uint8_t mac[6];
        WiFi.macAddress(mac);
        char macStr[18];
        sprintf(macStr, "%02X-%02X-%02X-%02X-%02X-%02X",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        deviceId = String("ESP32-") + String(macStr);
    }
    return deviceId;
}

void setup() {
    Serial.begin(115200);

    // Conectar WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando a WiFi...");
    }
    Serial.println("WiFi conectado");

    // Mostrar ID único del dispositivo
    deviceId = getDeviceId();
    Serial.print("ID del dispositivo: ");
    Serial.println(deviceId);

    // Configurar micrófono I2S
    setupMicrophone();

    Serial.println("ESP32 listo con sesiones independientes");
}

void sendAudioToAPI(uint8_t* audioData, size_t dataSize) {
    HTTPClient http;

    // Construir URL con session_id único
    String url = String(serverUrl) + deviceId;
    Serial.print("Enviando a: ");
    Serial.println(url);

    http.begin(url);
    http.addHeader("Content-Type", "application/octet-stream");

    Serial.println("Enviando audio...");
    int httpResponseCode = http.POST(audioData, dataSize);

    if (httpResponseCode > 0) {
        Serial.printf("Respuesta HTTP: %d\n", httpResponseCode);

        // Obtener respuesta de audio
        WiFiClient* stream = http.getStreamPtr();
        size_t responseSize = http.getSize();

        if (responseSize > 0) {
            Serial.printf("Recibida respuesta de %d bytes\n", responseSize);

            // Procesar respuesta de audio MP3
            uint8_t* responseBuffer = (uint8_t*)malloc(responseSize);
            if (responseBuffer) {
                size_t readBytes = stream->readBytes(responseBuffer, responseSize);
                Serial.printf("Leídos %d bytes de respuesta\n", readBytes);

                // Aquí reproducir el audio MP3
                // (requiere librería adicional para decodificar MP3)

                free(responseBuffer);
            }
        }
    } else {
        Serial.printf("Error HTTP: %d\n", httpResponseCode);
    }

    http.end();
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        // Simular envío periódico con session_id único
        static unsigned long lastSend = 0;
        if (millis() - lastSend > 10000) {  // Cada 10 segundos
            Serial.println("=== NUEVA CONVERSACIÓN ===");
            Serial.print("Sesión: ");
            Serial.println(deviceId);

            // Simular audio grabado
            uint8_t* audioBuffer = (uint8_t*)malloc(16000); // 1 segundo simulado
            for (int i = 0; i < 16000; i++) {
                audioBuffer[i] = random(0, 255);
            }

            sendAudioToAPI(audioBuffer, 16000);
            free(audioBuffer);

            lastSend = millis();
        }
    }

    delay(1000);
}

void setupMicrophone() {
    // Configuración I2S básica
    Serial.println("Configurando micrófono...");

    // Aquí iría la configuración real de I2S
    // Para INMP441 o similar
}

// Función adicional para obtener estadísticas
void getSessionStats() {
    HTTPClient http;
    String statsUrl = "http://192.168.1.100:8000/stats/sessions";

    http.begin(statsUrl);
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println("Estadísticas de sesiones:");
        Serial.println(payload);
    } else {
        Serial.printf("Error obteniendo estadísticas: %d\n", httpResponseCode);
    }

    http.end();
}

// Función para eliminar sesión (útil para testing)
void deleteSession() {
    HTTPClient http;
    String deleteUrl = "http://192.168.1.100:8000/sessions/" + deviceId;

    http.begin(deleteUrl);
    int httpResponseCode = http.DELETE();

    if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println("Sesión eliminada:");
        Serial.println(payload);
    } else {
        Serial.printf("Error eliminando sesión: %d\n", httpResponseCode);
    }

    http.end();
}