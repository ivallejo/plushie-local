# 🚀 Despliegue de AI Assistant API en Vercel

## 📋 Requisitos Previos

1. **Cuenta en Vercel**: [vercel.com](https://vercel.com)
2. **Cuenta en OpenAI**: [platform.openai.com](https://platform.openai.com)
3. **Git**: Para subir el código a un repositorio

## 🛠️ Configuración del Proyecto

### 1. Estructura del Proyecto
```
tu-proyecto/
├── api/
│   └── __init__.py          # API principal para Vercel
├── requirements.txt          # Dependencias Python
├── vercel.json              # Configuración de Vercel
├── .vercelignore           # Archivos a excluir
└── .env                    # Variables de entorno (local)
```

### 2. Variables de Entorno en Vercel

En el dashboard de Vercel, configura estas variables de entorno:

```bash
OPENAI_API_KEY=sk-proj-tu_clave_de_openai_aqui
ASSISTANT_ID=asst_tu_assistant_id_aqui
```

## 🚀 Despliegue Paso a Paso

### Opción 1: Despliegue desde GitHub

1. **Sube tu código a GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - AI Assistant API"
   git branch -M main
   git remote add origin https://github.com/tu-usuario/tu-repositorio.git
   git push -u origin main
   ```

2. **Conecta Vercel con GitHub**:
   - Ve a [vercel.com](https://vercel.com)
   - Click en "New Project"
   - Importa tu repositorio de GitHub
   - Vercel detectará automáticamente la configuración

3. **Configura las variables de entorno**:
   - Ve a Project Settings > Environment Variables
   - Agrega `OPENAI_API_KEY` y `ASSISTANT_ID`

4. **Deploy**:
   - Click en "Deploy"
   - Espera a que termine el proceso

### Opción 2: Despliegue desde CLI

1. **Instala Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login en Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy del proyecto**:
   ```bash
   vercel --prod
   ```

4. **Configura variables de entorno**:
   ```bash
   vercel env add OPENAI_API_KEY
   vercel env add ASSISTANT_ID
   ```

## 🔧 Configuración de Variables de Entorno

### En Vercel Dashboard:
1. Ve a tu proyecto
2. Project Settings > Environment Variables
3. Agrega:
   - `OPENAI_API_KEY`: Tu clave de OpenAI
   - `ASSISTANT_ID`: ID de tu asistente (opcional)

### Desde CLI:
```bash
vercel env add OPENAI_API_KEY production
vercel env add ASSISTANT_ID production
```

## 📡 Endpoints Disponibles

Una vez desplegado, tu API estará disponible en:
```
https://tu-proyecto.vercel.app
```

### Endpoints Principales:

#### Gestión de Usuarios:
```bash
POST /users                    # Crear usuario
GET  /users/{user_id}         # Obtener usuario
PUT  /users/{user_id}/ai-alias # Actualizar alias IA
```

#### Gestión de Dispositivos:
```bash
POST /devices                  # Registrar dispositivo
GET  /devices/{device_id}     # Obtener dispositivo
```

#### Procesamiento de Audio:
```bash
POST /process                  # Procesar audio (legacy)
POST /process/{session_id}     # Procesar audio con sesión
```

## 🧪 Pruebas del Despliegue

### 1. Crear un Usuario:
```bash
curl -X POST https://tu-proyecto.vercel.app/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Carlos Música",
    "email": "carlos@email.com",
    "ai_alias": "DJ Carlos",
    "custom_prompt": "Eres {ai_alias}, un asistente virtual especializado en música..."
  }'
```

### 2. Registrar un Dispositivo:
```bash
curl -X POST https://tu-proyecto.vercel.app/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32-SALA-CARLOS",
    "device_name": "ESP32 Sala Carlos",
    "location": "Sala de estar",
    "user_id": 1
  }'
```

### 3. Procesar Audio:
```bash
curl -X POST https://tu-proyecto.vercel.app/process/ESP32-SALA-CARLOS \
  -H "Content-Type: application/octet-stream" \
  --data-binary @tu_audio.wav \
  -o respuesta.mp3
```

## ⚠️ Limitaciones de Vercel

### Tiempo de Ejecución:
- **Máximo 30 segundos** por request
- Las funciones serverless tienen timeout

### Memoria:
- **Máximo 50MB** para el bundle
- **1GB RAM** disponible

### Almacenamiento:
- **No se puede escribir** en el sistema de archivos
- Los datos se pierden entre deployments
- Usamos almacenamiento en memoria

## 🔄 Actualizaciones

### Para actualizar tu API:
```bash
git add .
git commit -m "Update API"
git push origin main
```

Vercel detectará los cambios y redeploy automáticamente.

## 🐛 Solución de Problemas

### Error de Timeout:
- Reduce el `max_tokens` en la configuración de OpenAI
- Simplifica el procesamiento de audio

### Error de Memoria:
- Reduce el tamaño de los modelos
- Optimiza las dependencias en `requirements.txt`

### Error de Variables de Entorno:
- Verifica que las variables estén configuradas correctamente
- Redeploy después de cambiar variables

## 📊 Monitoreo

### Logs en Vercel:
1. Ve a tu proyecto en Vercel
2. Click en "Functions" para ver logs
3. Revisa errores y tiempos de respuesta

### Métricas:
- Número de requests
- Tiempos de respuesta
- Tasa de error

## 🎯 Próximos Pasos

1. **Configurar dominio personalizado**
2. **Agregar autenticación JWT**
3. **Implementar rate limiting**
4. **Agregar monitoreo avanzado**
5. **Configurar base de datos externa** (PostgreSQL/MySQL)

---

## 📞 Soporte

Si tienes problemas con el despliegue:

1. Revisa los logs de Vercel
2. Verifica las variables de entorno
3. Confirma que las dependencias estén correctas
4. Contacta soporte de Vercel si es necesario

¡Tu API de AI Assistant está lista para producción! 🚀