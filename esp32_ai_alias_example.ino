// ESP32 - Cliente con Gestión de Alias de IA Personalizado
// Cada usuario puede tener su propio nombre para la IA

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>

// Configuración WiFi
const char* ssid = "TU_WIFI_SSID";
const char* password = "TU_WIFI_PASSWORD";

// URL del servidor
const char* serverUrl = "http://192.168.1.100:8000";

// ID único del dispositivo (MAC Address)
String deviceId = "";
bool isRegistered = false;
int userId = -1; // ID del usuario asignado

// Función para obtener ID único del dispositivo
String getDeviceId() {
    if (deviceId == "") {
        uint8_t mac[6];
        WiFi.macAddress(mac);
        char macStr[18];
        sprintf(macStr, "%02X-%02X-%02X-%02X-%02X-%02X",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        deviceId = String("ESP32-") + String(macStr);
    }
    return deviceId;
}

// Función para crear usuario con ai_alias personalizado
bool createUserWithAIAlias(String name, String email, String aiAlias) {
    HTTPClient http;
    String url = String(serverUrl) + "/users";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    // Crear JSON con datos del usuario y ai_alias
    DynamicJsonDocument doc(1024);
    doc["name"] = name;
    doc["email"] = email;
    doc["ai_alias"] = aiAlias;

    // Preferencias por defecto
    JsonObject preferences = doc.createNestedObject("preferences");
    preferences["language"] = "es";
    preferences["voice_speed"] = 1.0;

    String jsonString;
    serializeJson(doc, jsonString);

    Serial.println("Creando usuario con AI alias...");
    Serial.println(jsonString);

    int httpResponseCode = http.POST(jsonString);

    if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println("Usuario creado:");
        Serial.println(payload);

        // Parsear respuesta para obtener user_id
        DynamicJsonDocument responseDoc(1024);
        deserializeJson(responseDoc, payload);
        userId = responseDoc["id"];

        http.end();
        return true;
    } else {
        Serial.printf("Error creando usuario: %d\n", httpResponseCode);
        http.end();
        return false;
    }
}

// Función para actualizar ai_alias de un usuario existente
bool updateUserAIAlias(int userId, String aiAlias) {
    HTTPClient http;
    String url = String(serverUrl) + "/users/" + String(userId) + "/ai-alias";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    // Crear JSON con el nuevo ai_alias
    DynamicJsonDocument doc(256);
    doc["ai_alias"] = aiAlias;

    String jsonString;
    serializeJson(doc, jsonString);

    Serial.println("Actualizando AI alias...");
    Serial.println(jsonString);

    int httpResponseCode = http.PUT(jsonString);

    if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println("AI alias actualizado:");
        Serial.println(payload);

        http.end();
        return true;
    } else {
        Serial.printf("Error actualizando AI alias: %d\n", httpResponseCode);
        http.end();
        return false;
    }
}

// Función para obtener información del usuario
bool getUserInfo(int userId) {
    HTTPClient http;
    String url = String(serverUrl) + "/users/" + String(userId);

    http.begin(url);
    int httpResponseCode = http.GET();

    if (httpResponseCode == 200) {
        String payload = http.getString();
        Serial.println("Información del usuario:");
        Serial.println(payload);

        // Parsear respuesta para mostrar el ai_alias
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, payload);

        if (doc.containsKey("ai_alias") && !doc["ai_alias"].isNull()) {
            String aiAlias = doc["ai_alias"];
            Serial.print("AI Alias actual: ");
            Serial.println(aiAlias);
        }

        http.end();
        return true;
    } else {
        Serial.printf("Error obteniendo usuario: %d\n", httpResponseCode);
        http.end();
        return false;
    }
}

// Función para registrar dispositivo
bool registerDevice(String deviceName, String location) {
    HTTPClient http;
    String url = String(serverUrl) + "/devices";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    // Crear JSON con datos del dispositivo
    DynamicJsonDocument doc(1024);
    doc["device_id"] = deviceId;
    doc["device_name"] = deviceName;
    doc["device_type"] = "ESP32";
    doc["location"] = location;
    doc["mac_address"] = deviceId; // Usar deviceId como MAC simplificado

    if (userId != -1) {
        doc["user_id"] = userId;
    }

    String jsonString;
    serializeJson(doc, jsonString);

    Serial.println("Registrando dispositivo...");
    Serial.println(jsonString);

    int httpResponseCode = http.POST(jsonString);

    if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println("Dispositivo registrado:");
        Serial.println(payload);

        isRegistered = true;
        http.end();
        return true;
    } else {
        Serial.printf("Error registrando dispositivo: %d\n", httpResponseCode);
        http.end();
        return false;
    }
}

// Función para verificar registro del dispositivo
bool checkDeviceRegistration() {
    HTTPClient http;
    String url = String(serverUrl) + "/devices/" + deviceId;

    http.begin(url);
    int httpResponseCode = http.GET();

    if (httpResponseCode == 200) {
        String payload = http.getString();
        Serial.println("Dispositivo ya registrado:");
        Serial.println(payload);

        // Parsear respuesta
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, payload);

        if (doc.containsKey("user_id") && !doc["user_id"].isNull()) {
            userId = doc["user_id"];
        }

        isRegistered = true;
        http.end();
        return true;
    } else if (httpResponseCode == 404) {
        Serial.println("Dispositivo no registrado, procediendo con registro...");
        http.end();
        return false;
    } else {
        Serial.printf("Error verificando dispositivo: %d\n", httpResponseCode);
        http.end();
        return false;
    }
}

// Función para enviar audio con session_id
void sendAudioToAPI(uint8_t* audioData, size_t dataSize) {
    HTTPClient http;
    String url = String(serverUrl) + "/process/" + deviceId;

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

void setup() {
    Serial.begin(115200);

    // Conectar WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando a WiFi...");
    }
    Serial.println("WiFi conectado");

    // Obtener ID único del dispositivo
    deviceId = getDeviceId();
    Serial.print("ID del dispositivo: ");
    Serial.println(deviceId);

    // Verificar si el dispositivo ya está registrado
    if (!checkDeviceRegistration()) {
        // Si no está registrado, crear usuario con ai_alias personalizado
        Serial.println("Iniciando proceso de registro...");

        // Crear usuario con ai_alias personalizado
        if (createUserWithAIAlias("Pedro Gómez", "pedro@email.com", "Chef Pedro")) {
            Serial.println("Usuario creado exitosamente con AI alias");

            // Registrar dispositivo
            if (registerDevice("ESP32 Cocina Pedro", "Cocina Principal")) {
                Serial.println("Dispositivo registrado exitosamente");
            } else {
                Serial.println("Error registrando dispositivo");
            }
        } else {
            Serial.println("Error creando usuario");
        }
    } else {
        Serial.println("Dispositivo ya estaba registrado");

        // Mostrar información del usuario
        if (userId != -1) {
            getUserInfo(userId);
        }
    }

    // Configurar micrófono I2S
    setupMicrophone();

    Serial.println("ESP32 listo con AI alias personalizado");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED && isRegistered) {
        // Simular envío periódico
        static unsigned long lastSend = 0;
        if (millis() - lastSend > 20000) {  // Cada 20 segundos
            Serial.println("=== NUEVA CONVERSACIÓN CON AI ALIAS PERSONALIZADO ===");
            Serial.print("Usuario: ");
            Serial.println(userId);
            Serial.print("Dispositivo: ");
            Serial.println(deviceId);

            // Simular audio grabado
            uint8_t* audioBuffer = (uint8_t*)malloc(16000);
            for (int i = 0; i < 16000; i++) {
                audioBuffer[i] = random(0, 255);
            }

            sendAudioToAPI(audioBuffer, 16000);
            free(audioBuffer);

            lastSend = millis();
        }

        // Ejemplo: Cambiar AI alias cada cierto tiempo (solo para demo)
        static unsigned long lastAliasChange = 0;
        if (millis() - lastAliasChange > 60000) {  // Cada minuto
            String newAlias = "Master Chef " + String(random(1, 100));
            if (updateUserAIAlias(userId, newAlias)) {
                Serial.println("AI Alias actualizado para demo");
            }
            lastAliasChange = millis();
        }
    }

    delay(1000);
}

void setupMicrophone() {
    Serial.println("Configurando micrófono...");
    // Configuración I2S aquí
}