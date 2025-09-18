# 🎨 Despliegue de AI Assistant API en Render

## 📋 Requisitos Previos

1. **Cuenta en Render**: [render.com](https://render.com)
2. **Cuenta en OpenAI**: [platform.openai.com](https://platform.openai.com)
3. **Cuenta en GitHub**: Para conectar el repositorio

## 🛠️ Configuración del Proyecto para Render

### **Estructura del Proyecto**
```
📦 ai-assistant-render/
├── 📄 requirements.txt              # ✅ Dependencias completas (incluye Whisper)
├── 📄 render.yaml                   # ✅ Configuración de Render
├── 📄 .gitignore                    # ✅ Exclusiones actualizadas
├── 📄 RENDER_DEPLOYMENT.md          # ✅ Esta guía
├── 📄 deploy_to_render.sh           # ✅ Script de despliegue automatizado
├── 📁 api/
│   └── 📄 __init__.py              # ✅ API completa con Whisper
└── 📄 .env                         # Variables de entorno locales
```

### **Dependencias Optimizadas para Render**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
openai==1.107.3
openai-whisper>=20231117      # ✅ Whisper completo soportado
gtts==2.5.1
numpy==2.2.6
soundfile==0.13.1
psycopg2-binary==2.9.7        # ✅ PostgreSQL para Render
python-dotenv==1.1.1
pydantic==2.5.0
python-multipart==0.0.6
```

## 🚀 Despliegue Paso a Paso

### **Opción 1: Despliegue Automático (Recomendado)**

#### **Paso 1: Ejecutar el script automatizado**
```bash
# Hacer ejecutable el script
chmod +x deploy_to_render.sh

# Ejecutar despliegue
./deploy_to_render.sh
```

#### **Paso 2: El script hace automáticamente:**
- ✅ Verifica repositorio Git
- ✅ Crea commit con cambios
- ✅ Sube a GitHub
- ✅ Muestra instrucciones para Render

### **Opción 2: Despliegue Manual desde Render Dashboard**

#### **Paso 1: Crear cuenta en Render**
1. Ve a [render.com](https://render.com)
2. **Regístrate** con GitHub (te da $5 extra automáticamente)
3. **Verifica** tu email

#### **Paso 2: Crear Web Service**
1. En Render dashboard: **"New"** → **"Web Service"**
2. **"Connect"** → **GitHub**
3. **Busca y selecciona:** `ivallejo/plushie-local`
4. Click **"Connect"**

#### **Paso 3: Configurar Servicio**
```yaml
# Render detectará automáticamente o configura manualmente:
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python api/__init__.py
```

#### **Paso 4: Variables de Entorno**
En **"Environment"** agrega:
```bash
OPENAI_API_KEY=sk-proj-tu_clave_de_openai_aqui
ASSISTANT_ID=asst_tu_assistant_id_aqui
```

#### **Paso 5: Base de Datos PostgreSQL**
1. En Render: **"New"** → **"PostgreSQL"**
2. **Plan:** Free (256MB)
3. **Region:** Selecciona la más cercana
4. **Create database**
5. **Conectar** a tu web service:
   - Ve a tu web service
   - **"Environment"** → **"Add from PostgreSQL"**
   - Selecciona tu base de datos

#### **Paso 6: Deploy**
1. Click **"Create Web Service"**
2. Render hace el build automáticamente
3. **Monitorea logs** en tiempo real
4. **Espera 5-10 minutos** para el primer despliegue

## 🎯 Características de Render para tu AI Assistant

### **✅ Ventajas sobre otras plataformas:**
- **2GB RAM** (vs 1GB Vercel) → Whisper funciona perfectamente
- **750 horas gratis/mes** → Suficiente para desarrollo
- **PostgreSQL incluido** gratis → Persistencia de datos
- **Auto-scaling** automático → Maneja picos de carga
- **Deploy desde GitHub** → Actualizaciones automáticas

### **✅ Recursos Gratis en Render:**
- **750 horas/mes** de compute
- **2GB RAM** por servicio
- **PostgreSQL 256MB** gratis
- **Bandwidth ilimitado**
- **Deploy automático** desde GitHub
- **SSL automático** incluido

## 📊 Progreso de Despliegue Esperado

### **Fase 1: Build (3-5 minutos)**
```
🔨 Cloning repository...
🔨 Installing Python dependencies...
🔨 Installing openai-whisper (funciona con 2GB RAM)
🔨 Build completed successfully
```

### **Fase 2: Deploy (2-3 minutos)**
```
🚀 Starting deployment...
🚀 PostgreSQL connected
🚀 Application starting...
🚀 Deployment completed!
```

### **Fase 3: URL de Producción**
```
🌐 https://tu-proyecto.onrender.com
```

## 🧪 Pruebas Post-Despliegue

### **Verificar que funciona:**
```bash
# 1. Probar endpoint raíz
curl https://tu-proyecto.onrender.com/
# Respuesta: {"message": "AI Assistant API", "version": "1.0.0"}

# 2. Crear usuario con AI Alias
curl -X POST https://tu-proyecto.onrender.com/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Carlos Música",
    "ai_alias": "DJ Carlos",
    "custom_prompt": "Eres {ai_alias}, un asistente musical..."
  }'

# 3. Probar procesamiento de audio
curl -X POST https://tu-proyecto.onrender.com/process/ESP32-CARLOS \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test_audio.wav \
  -o respuesta.mp3
```

## 📊 Monitoreo y Logs

### **Ver logs en tiempo real:**
- Ve a tu servicio en Render
- Click en **"Logs"** en la parte superior
- Verás logs del build y runtime

### **Métricas disponibles:**
- 📈 **Uso de CPU/RAM**
- 🌐 **Requests por hora**
- ⚡ **Tiempo de respuesta**
- 💰 **Horas utilizadas**

## 🔧 Configuración Avanzada

### **Variables de Entorno Adicionales:**
```bash
# Configuración de Whisper
WHISPER_MODEL=tiny          # tiny, base, small, medium, large
WHISPER_LANGUAGE=es         # Idioma por defecto

# Configuración de OpenAI
OPENAI_MODEL=gpt-3.5-turbo  # gpt-3.5-turbo, gpt-4
OPENAI_MAX_TOKENS=100       # Máximo tokens por respuesta

# Configuración de TTS
TTS_LANG=es                 # Idioma de gTTS
TTS_SLOW=False             # Velocidad de habla
```

### **Escalado Automático:**
Render escala automáticamente basado en:
- **CPU usage** > 70%
- **RAM usage** > 80%
- **Request rate** > umbral

## 💰 Precios y Costos

### **Plan Free (Recomendado para desarrollo)**
- **750 horas/mes** gratis
- **2GB RAM** incluido
- **PostgreSQL 256MB** gratis
- **Después de 750 horas:** $7/mes

### **Plan Individual**
- **$7/mes** (sin límites de horas)
- **2GB RAM** incluido
- **PostgreSQL 1GB** incluido
- **Dominio personalizado** incluido

## 🚨 Solución de Problemas

### **Problema: Build falla**
```bash
# Ver logs detallados en Render dashboard
# Posibles soluciones:
# 1. Verificar requirements.txt
# 2. Aumentar timeout si es necesario
# 3. Verificar variables de entorno
```

### **Problema: Whisper no funciona**
```bash
# Verificar que tienes suficiente RAM
# En logs deberías ver: "2GB RAM available"
# Si no, considera upgrade a plan Individual
```

### **Problema: Base de datos**
```bash
# Verificar conexión PostgreSQL
# En logs: "Database connected successfully"
# Si no, verifica DATABASE_URL
```

### **Problema: Timeout**
```bash
# Render tiene timeout de 30 segundos
# Optimiza tu código para respuestas rápidas
# Considera usar WebSockets para respuestas largas
```

## 🎯 Próximos Pasos

### **Después del despliegue exitoso:**
1. ✅ **Conectar ESP32** con la nueva URL
2. ✅ **Probar AI Aliases** personalizados
3. ✅ **Configurar monitoreo** continuo
4. ✅ **Optimizar costos** según uso

### **Mejoras futuras:**
- 🔄 **Migrar a Redis** para cache distribuido
- 📊 **Agregar métricas avanzadas**
- 🔐 **Implementar autenticación JWT**
- 🌐 **Configurar dominio personalizado**

## 📞 Soporte

### **Recursos de ayuda:**
- 📚 **Documentación**: [docs.render.com](https://docs.render.com)
- 💬 **Discord**: [render.com/discord](https://render.com/discord)
- 🐛 **GitHub Issues**: [github.com/renderinc](https://github.com/renderinc)

### **Comandos útiles:**
```bash
# Ver estado del servicio
render services list

# Ver logs
render logs

# Reiniciar servicio
render restart
```

---

## 🎉 ¡Tu AI Assistant está listo en Render!

Con Render tienes:
- ✅ **Whisper funcionando** perfectamente
- ✅ **2GB RAM** suficiente para todo
- ✅ **PostgreSQL incluido** gratis
- ✅ **750 horas gratis** por mes
- ✅ **Deploy automático** desde GitHub

¡Tu **AI Assistant API con AI Alias personalizados y Whisper completo** está ahora desplegada en una plataforma que puede manejar todas las dependencias pesadas! 🚀

¿Ya creaste tu cuenta en Render? ¿Necesitas ayuda con algún paso específico del despliegue?