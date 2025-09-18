# 🔐 Gestión de Sesiones por Usuario - Arquitectura Multi-Usuario

## 🎯 PROBLEMA IDENTIFICADO

**Necesidad:** 10 usuarios (ESP32) con conversaciones independientes
- Cada placa debe mantener su propio historial
- Conversaciones no deben mezclarse
- Identificador único por dispositivo

## 🏗️ SOLUCIÓN PROPUESTA

### **1. Identificador Único por Dispositivo**

#### **Opción A: MAC Address del ESP32**
```cpp
// ESP32 - Obtener MAC Address
#include <WiFi.h>

String getDeviceId() {
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char macStr[18];
    sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X",
            mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return String(macStr);
}

// Uso:
String deviceId = getDeviceId(); // "A4:CF:12:8B:3F:9E"
```

#### **Opción B: UUID Personalizado**
```cpp
// Generar UUID único por dispositivo
#include <ESP32UUID.h>

String deviceId = ESP32UUID::generateUUID();
```

#### **Opción C: ID en EEPROM**
```cpp
// Almacenar ID único en EEPROM
#include <EEPROM.h>

#define EEPROM_SIZE 64
#define DEVICE_ID_ADDR 0

String getOrCreateDeviceId() {
    EEPROM.begin(EEPROM_SIZE);

    // Leer ID existente
    String deviceId = "";
    for (int i = 0; i < 36; i++) {
        char c = EEPROM.read(DEVICE_ID_ADDR + i);
        if (c != 0xFF) deviceId += c;
    }

    // Si no existe, crear uno
    if (deviceId.length() == 0) {
        deviceId = "ESP32-" + String(random(100000, 999999));
        for (int i = 0; i < deviceId.length(); i++) {
            EEPROM.write(DEVICE_ID_ADDR + i, deviceId[i]);
        }
        EEPROM.commit();
    }

    return deviceId;
}
```

### **2. API con Soporte de Sesiones**

#### **Endpoint Actualizado**
```python
# api.py - Endpoint con session_id
@app.post("/process/{session_id}")
async def process_with_session(session_id: str, request: Request):
    audio = await request.body()
    return Response(
        content=await process_audio(audio, session_id),
        media_type="audio/mp3"
    )

# Mantener compatibilidad con endpoint anterior
@app.post("/process")
async def process_legacy(request: Request):
    audio = await request.body()
    # Usar session_id por defecto para compatibilidad
    return Response(
        content=await process_audio(audio, "default_session"),
        media_type="audio/mp3"
    )
```

#### **Función process_audio Actualizada**
```python
async def process_audio(audio_data: bytes, session_id: str = "default_session"):
    start_time = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Iniciando procesamiento...")

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
    cache_key = f"{session_id}:{texto}"
    cursor = conn.cursor()
    cursor.execute("SELECT output FROM cache WHERE input = ?", (cache_key,))
    cached = cursor.fetchone()
    if cached:
        print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Respuesta desde caché")
        return cached[0]

    # Historial de conversación por sesión
    cursor.execute("SELECT messages FROM conversations WHERE session_id = ?", (session_id,))
    result = cursor.fetchone()

    if result:
        conversation_history = json.loads(result[0])
    else:
        conversation_history = [{
            "role": "system",
            "content": f"Eres un asistente virtual claro y directo para el dispositivo {session_id}. Responde de manera concisa, útil y en español. Evita explicaciones largas y ve al grano."
        }]

    # Agregar mensaje del usuario
    conversation_history.append({"role": "user", "content": texto})

    # Mantener solo los últimos 20 mensajes
    if len(conversation_history) > 21:
        conversation_history = [conversation_history[0]] + conversation_history[-20:]

    # LLM con historial de sesión
    llm_start = time.time()
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=100,
        temperature=0.3,
        timeout=10.0
    )

    respuesta = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": respuesta})

    # Guardar conversación de la sesión
    cursor.execute("""
        INSERT OR REPLACE INTO conversations (session_id, messages, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (session_id, json.dumps(conversation_history)))
    conn.commit()

    llm_time = time.time() - llm_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - LLM: '{respuesta}' ({llm_time:.2f}s)")

    # TTS
    tts_start = time.time()
    tts = gTTS(text=respuesta, lang='es')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    audio_out = audio_io.getvalue()
    tts_time = time.time() - tts_start
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - TTS: {len(audio_out)} bytes ({tts_time:.2f}s)")

    # Guardar en caché con session_id
    cursor.execute("INSERT OR REPLACE INTO cache (input, output) VALUES (?, ?)", (cache_key, audio_out))
    conn.commit()

    total_time = time.time() - start_time
    print(f"[{time.strftime('%H:%M:%S')}] Sesión: {session_id} - Total: {total_time:.2f}s")

    return audio_out
```

### **3. Cliente ESP32 con Session ID**

#### **Código ESP32 Actualizado**
```cpp
// ESP32 - Cliente con Session ID único
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// Configuración
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://192.168.1.100:8000/process/"; // Base URL

// ID único del dispositivo
String deviceId = "";

// Función para obtener ID único
String getDeviceId() {
    if (deviceId == "") {
        // Opción 1: Usar MAC Address
        uint8_t mac[6];
        WiFi.macAddress(mac);
        char macStr[18];
        sprintf(macStr, "%02X-%02X-%02X-%02X-%02X-%02X",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        deviceId = String("ESP32-") + String(macStr);

        // Opción 2: ID personalizado
        // deviceId = "ESP32-KITCHEN-001";
    }
    return deviceId;
}

void setup() {
    Serial.begin(115200);

    // Conectar WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando WiFi...");
    }
    Serial.println("WiFi conectado");

    // Mostrar ID del dispositivo
    deviceId = getDeviceId();
    Serial.print("ID del dispositivo: ");
    Serial.println(deviceId);

    // Configurar I2S para micrófono
    setupMicrophone();
}

void sendAudioToAPI(uint8_t* audioData, size_t dataSize) {
    HTTPClient http;

    // Construir URL con session_id
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

            // Procesar respuesta de audio
            uint8_t* responseBuffer = (uint8_t*)malloc(responseSize);
            if (responseBuffer) {
                size_t readBytes = stream->readBytes(responseBuffer, responseSize);
                Serial.printf("Leídos %d bytes de respuesta\n", readBytes);

                // Aquí reproducir el audio MP3
                // (requiere librería adicional)

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
        // Simular envío periódico
        static unsigned long lastSend = 0;
        if (millis() - lastSend > 15000) {  // Cada 15 segundos
            Serial.println("=== NUEVA CONVERSACIÓN ===");

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
    // Configuración I2S
    Serial.println("Configurando micrófono...");
    // Configuración real aquí
}
```

### **4. Base de Datos con Sesiones**

#### **Actualizar Esquema de Base de Datos**
```sql
-- Tabla de conversaciones por sesión
CREATE TABLE conversations (
    session_id VARCHAR(255) PRIMARY KEY,
    messages JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device_info JSONB  -- Información adicional del dispositivo
);

-- Tabla de caché por sesión
CREATE TABLE cache (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    input_text TEXT,
    output_data BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    UNIQUE(session_id, input_hash)
);

-- Índices optimizados
CREATE INDEX idx_conversations_session_updated ON conversations(session_id, updated_at DESC);
CREATE INDEX idx_cache_session_hash ON cache(session_id, input_hash);
CREATE INDEX idx_cache_session_accessed ON cache(session_id, last_accessed DESC);
```

### **5. Monitoreo de Sesiones**

#### **Endpoint de Estadísticas**
```python
@app.get("/stats/sessions")
async def get_session_stats():
    cursor = conn.cursor()

    # Estadísticas generales
    cursor.execute("""
        SELECT
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(*) as total_conversations,
            AVG(jsonb_array_length(messages)) as avg_messages_per_session,
            MAX(updated_at) as last_activity
        FROM conversations
    """)

    stats = cursor.fetchone()

    # Sesiones activas (últimas 24 horas)
    cursor.execute("""
        SELECT session_id, updated_at,
               jsonb_array_length(messages) as message_count
        FROM conversations
        WHERE updated_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ORDER BY updated_at DESC
        LIMIT 10
    """)

    active_sessions = cursor.fetchall()

    return {
        "total_sessions": stats[0],
        "total_conversations": stats[1],
        "avg_messages_per_session": float(stats[2]) if stats[2] else 0,
        "last_activity": stats[3],
        "active_sessions": [
            {
                "session_id": session[0],
                "last_activity": session[1],
                "message_count": session[2]
            } for session in active_sessions
        ]
    }
```

### **6. Limpieza de Sesiones Inactivas**

#### **Función de Mantenimiento**
```python
@app.post("/admin/cleanup-sessions")
async def cleanup_old_sessions(days: int = 30):
    """Eliminar sesiones inactivas"""
    cursor = conn.cursor()

    # Eliminar conversaciones antiguas
    cursor.execute("""
        DELETE FROM conversations
        WHERE updated_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
    """, (days,))

    conversations_deleted = cursor.rowcount

    # Eliminar caché de sesiones eliminadas
    cursor.execute("""
        DELETE FROM cache
        WHERE session_id NOT IN (
            SELECT session_id FROM conversations
        )
    """)

    cache_deleted = cursor.rowcount
    conn.commit()

    return {
        "conversations_deleted": conversations_deleted,
        "cache_deleted": cache_deleted,
        "message": f"Limpieza completada: {conversations_deleted} conversaciones y {cache_deleted} entradas de caché eliminadas"
    }
```

## 🎯 EJEMPLOS DE USO

### **1. ESP32 Cocina**
```cpp
// ID: ESP32-A4CF128B3F9E
// Conversación: "¿Qué receta puedo hacer con los ingredientes que tengo?"
```

### **2. ESP32 Sala**
```cpp
// ID: ESP32-B8D7432A1F5C
// Conversación: "¿Cuál es el clima hoy?"
```

### **3. ESP32 Dormitorio**
```cpp
// ID: ESP32-C9E8543B2G6D
// Conversación: "¿Qué hora es?"
```

## 🔒 SEGURIDAD Y PRIVACIDAD

### **Consideraciones de Seguridad**
- ✅ **Sesiones aisladas** - No hay cruce de conversaciones
- ✅ **IDs únicos** - Cada dispositivo tiene su propio identificador
- ✅ **Limpieza automática** - Sesiones inactivas se eliminan
- ✅ **Auditoría** - Logs por sesión para debugging

### **Privacidad**
- ✅ **Datos separados** - Cada sesión tiene su propio historial
- ✅ **No compartido** - Conversaciones no se mezclan
- ✅ **Controlable** - Usuario puede eliminar su sesión

## 📊 ESCALABILIDAD

### **Para 10 Usuarios**
- ✅ **SQLite:** Suficiente para desarrollo
- ✅ **PostgreSQL:** Recomendado para producción
- ✅ **Sesiones independientes:** Sin conflictos
- ✅ **Monitoreo:** Estadísticas por sesión

### **Para Más Usuarios**
- 🔄 **Sharding por session_id**
- 🔄 **Redis para caché distribuida**
- 🔄 **Load balancing**

---

## 🚀 IMPLEMENTACIÓN RECOMENDADA

### **Paso 1: Actualizar API**
```python
# Agregar endpoint con session_id
@app.post("/process/{session_id}")
async def process_with_session(session_id: str, request: Request):
    audio = await request.body()
    return Response(
        content=await process_audio(audio, session_id),
        media_type="audio/mp3"
    )
```

### **Paso 2: Actualizar ESP32**
```cpp
// Usar MAC Address como session_id
String sessionId = getDeviceId();
String url = "http://servidor:8000/process/" + sessionId;
```

### **Paso 3: Probar**
```bash
# Probar con session_id específico
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test.wav \
  http://localhost:8000/process/ESP32-A4CF128B3F9E
```

**Resultado:** Cada ESP32 tendrá su propia conversación independiente y persistente. 🎯