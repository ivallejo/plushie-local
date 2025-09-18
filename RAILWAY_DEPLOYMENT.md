# 🚂 Despliegue de AI Assistant API en Railway

## 📋 Requisitos Previos

1. **Cuenta en Railway**: [railway.app](https://railway.app)
2. **Cuenta en OpenAI**: [platform.openai.com](https://platform.openai.com)
3. **Railway CLI** (opcional pero recomendado):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

## 🛠️ Configuración del Proyecto para Railway

### **Estructura del Proyecto**
```
📦 ai-assistant-railway/
├── 📄 requirements.txt              # ✅ Dependencias completas (incluye Whisper)
├── 📄 railway.json                  # ✅ Configuración de Railway
├── 📄 .gitignore                    # ✅ Exclusiones actualizadas
├── 📄 RAILWAY_DEPLOYMENT.md         # ✅ Esta guía
├── 📄 deploy_to_railway.sh          # ✅ Script de despliegue automatizado
├── 📁 api/
│   └── 📄 __init__.py              # ✅ API completa con Whisper
└── 📄 .env                         # Variables de entorno locales
```

### **Dependencias Optimizadas para Railway**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
openai==1.107.3
openai-whisper>=20231117      # ✅ Whisper completo soportado
gtts==2.5.1
numpy==2.2.6
soundfile==0.13.1
psycopg2-binary==2.9.7        # ✅ PostgreSQL incluido
python-dotenv==1.1.1
pydantic==2.5.0
python-multipart==0.0.6
```

## 🚀 Despliegue Paso a Paso

### **Opción 1: Despliegue Automático (Recomendado)**

#### **Paso 1: Ejecutar el script automatizado**
```bash
# Hacer ejecutable el script
chmod +x deploy_to_railway.sh

# Ejecutar despliegue
./deploy_to_railway.sh
```

#### **Paso 2: El script hace automáticamente:**
- ✅ Verifica Railway CLI
- ✅ Confirma repositorio Git
- ✅ Crea commit con cambios
- ✅ Despliega a Railway
- ✅ Muestra URL de producción

### **Opción 2: Despliegue Manual desde Railway Dashboard**

#### **Paso 1: Crear proyecto en Railway**
1. Ve a [railway.app](https://railway.app)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Busca y selecciona: `ivallejo/plushie-local`
5. Click en **"Deploy"**

#### **Paso 2: Configurar variables de entorno**
En el dashboard de Railway, ve a **"Variables"** y agrega:

```bash
OPENAI_API_KEY=sk-proj-tu_clave_de_openai_aqui
ASSISTANT_ID=asst_tu_assistant_id_aqui
```

#### **Paso 3: Configurar base de datos**
Railway incluye PostgreSQL automáticamente:
1. En tu proyecto, ve a **"Database"**
2. Railway crea automáticamente una instancia PostgreSQL
3. La variable `DATABASE_URL` se configura automáticamente

### **Opción 3: Despliegue desde CLI**

#### **Paso 1: Login en Railway**
```bash
railway login
```

#### **Paso 2: Conectar repositorio**
```bash
# Si no tienes proyecto
railway init

# Conectar con GitHub
railway connect
```

#### **Paso 3: Configurar variables**
```bash
railway variables set OPENAI_API_KEY=tu_clave_aqui
railway variables set ASSISTANT_ID=tu_assistant_id_aqui
```

#### **Paso 4: Deploy**
```bash
railway up
```

## 🎯 Características de Railway para tu AI Assistant

### **✅ Ventajas sobre Vercel**
- 🚀 **8GB RAM** (vs 1GB en Vercel)
- 💾 **PostgreSQL incluido** gratis
- ⚡ **Whisper funciona perfectamente**
- 🔄 **Auto-scaling** inteligente
- 🌍 **Deploy global** optimizado

### **✅ Recursos incluidos**
- **CPU**: Compartido a dedicado según uso
- **RAM**: Hasta 8GB
- **Disco**: 1GB incluido
- **Bandwidth**: Ilimitado
- **PostgreSQL**: 1GB incluido

## 🧪 Pruebas Post-Despliegue

### **Verificar que funciona:**
```bash
# 1. Obtener URL de Railway
railway open

# 2. Probar endpoint raíz
curl https://tu-proyecto.railway.app/

# 3. Crear usuario de prueba
curl -X POST https://tu-proyecto.railway.app/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Carlos Música",
    "ai_alias": "DJ Carlos",
    "custom_prompt": "Eres {ai_alias}, un asistente musical..."
  }'

# 4. Probar procesamiento de audio
curl -X POST https://tu-proyecto.railway.app/process/test-device \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test_audio.wav \
  -o respuesta.mp3
```

## 📊 Monitoreo y Logs

### **Ver logs en tiempo real:**
```bash
# Desde CLI
railway logs

# Desde dashboard
# Ve a tu proyecto → "Logs"
```

### **Métricas disponibles:**
- 📈 **Uso de CPU/RAM**
- 🌐 **Requests por minuto**
- ⚡ **Tiempo de respuesta**
- 💰 **Costo estimado**

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
Railway escala automáticamente basado en:
- **CPU usage** > 70%
- **RAM usage** > 80%
- **Request queue** > 10

## 💰 Precios y Costos

### **Plan Hobby (Recomendado para desarrollo)**
- **$5/mes** base
- **512MB RAM** incluido
- **PostgreSQL 512MB** incluido
- **Escalado automático** disponible

### **Plan Pro**
- **$10/mes** base
- **8GB RAM** incluido
- **PostgreSQL 1GB** incluido
- **CPU dedicada** disponible

### **Pago por uso:**
- **CPU**: $0.000463/hora
- **RAM**: $0.000231/GB-hora
- **Bandwidth**: $0.10/GB

## 🚨 Solución de Problemas

### **Problema: Build falla**
```bash
# Ver logs detallados
railway logs --build

# Reiniciar build
railway up --detach
```

### **Problema: Whisper no funciona**
```bash
# Verificar que las dependencias se instalaron
railway run pip list | grep whisper

# Verificar memoria disponible
railway run python -c "import psutil; print(psutil.virtual_memory())"
```

### **Problema: Base de datos**
```bash
# Ver variables de entorno
railway variables

# Conectar a PostgreSQL
railway connect postgresql
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
- 📚 **Documentación**: [docs.railway.app](https://docs.railway.app)
- 💬 **Discord**: [railway.app/discord](https://railway.app/discord)
- 🐛 **GitHub Issues**: [github.com/railwayapp/cli](https://github.com/railwayapp/cli)

### **Comandos útiles:**
```bash
# Ver estado del proyecto
railway status

# Ver uso de recursos
railway usage

# Reiniciar aplicación
railway restart

# Ver variables de entorno
railway variables
```

---

## 🎉 ¡Tu AI Assistant está listo en Railway!

Con Railway tienes:
- ✅ **Whisper funcionando** perfectamente
- ✅ **PostgreSQL incluido** gratis
- ✅ **Auto-scaling** inteligente
- ✅ **Deploy global** optimizado
- ✅ **AI Aliases** personalizados funcionando

¡Tu API de AI Assistant con AI Alias personalizados está ahora desplegada en una plataforma que puede manejar todas las dependencias pesadas! 🚀