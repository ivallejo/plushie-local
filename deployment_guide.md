# 🚀 Guía de Despliegue - Asistente Virtual

## 🎯 ESTRATEGIAS DE DESPLIEGUE POR ESCALA

### **📊 Matriz de Decisión**

| Factor | Vercel | Heroku | Cloud Run | AWS EC2 | AWS Lambda |
|--------|--------|--------|-----------|---------|------------|
| **Facilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Costo** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Escalabilidad** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Personalización** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Mantenimiento** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 🌟 DESPLIEGUE RÁPIDO CON VERCEL (RECOMENDADO)

### **1. Preparar el Proyecto**
```bash
# Crear requirements.txt
echo "fastapi==0.104.1
uvicorn[standard]==0.24.0
openai==1.107.3
gtts==2.5.0
whisper-openai==20240930
torch==2.8.0
numpy==2.2.6
python-dotenv==1.1.1" > requirements.txt

# Crear vercel.json
cat > vercel.json << EOF
{
  "version": 2,
  "builds": [
    {
      "src": "api.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "500mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api.py"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai-api-key"
  }
}
EOF
```

### **2. Desplegar**
```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Desplegar
vercel --prod

# Agregar variables de entorno
vercel env add OPENAI_API_KEY
```

### **3. URL de Producción**
```
https://tu-proyecto.vercel.app/process
```

---

## 🐙 DESPLIEGUE CON HEROKU (ESCALABLE)

### **1. Preparar para Heroku**
```bash
# Crear Procfile
echo "web: uvicorn api:app --host=0.0.0.0 --port=\$PORT" > Procfile

# Crear runtime.txt
echo "python-3.11.7" > runtime.txt

# Crear .env.example
cat > .env.example << EOF
OPENAI_API_KEY=tu_clave_aqui
DATABASE_URL=postgresql://...
EOF
```

### **2. Configurar PostgreSQL**
```bash
# Agregar PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Obtener URL de base de datos
heroku config:get DATABASE_URL
```

### **3. Desplegar**
```bash
# Crear app
heroku create tu-asistente-virtual

# Configurar variables
heroku config:set OPENAI_API_KEY="tu_clave"

# Desplegar
git push heroku main
```

### **4. Verificar**
```bash
# Ver logs
heroku logs --tail

# Probar endpoint
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test.wav \
  https://tu-app.herokuapp.com/process
```

---

## 🐳 DESPLIEGUE CON GOOGLE CLOUD RUN

### **1. Crear Dockerfile**
```dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app
USER app

WORKDIR /home/app

# Copiar requirements primero para cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/docs || exit 1

# Comando de inicio
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **2. Construir y Desplegar**
```bash
# Construir imagen
gcloud builds submit --tag gcr.io/PROJECT-ID/asistente-virtual

# Desplegar en Cloud Run
gcloud run deploy asistente-virtual \
  --image gcr.io/PROJECT-ID/asistente-virtual \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY="tu_clave" \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --concurrency 80
```

### **3. Configurar Base de Datos**
```bash
# Crear instancia de Cloud SQL
gcloud sql instances create asistente-db \
  --database-version POSTGRES_14 \
  --region us-central1 \
  --tier db-f1-micro

# Conectar a Cloud Run
gcloud run services update asistente-virtual \
  --add-cloudsql-instances PROJECT-ID:us-central1:asistente-db \
  --set-env-vars DATABASE_URL="postgresql://..."
```

---

## ☁️ DESPLIEGUE SERVERLESS CON AWS LAMBDA

### **1. Crear Función Lambda**
```python
# lambda_function.py
import json
import base64
from api import process_audio

def lambda_handler(event, context):
    try:
        # Decodificar audio de base64
        audio_data = base64.b64decode(event['body'])

        # Procesar audio
        result = process_audio(audio_data)

        # Retornar respuesta
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'audio/mp3',
                'Access-Control-Allow-Origin': '*'
            },
            'body': base64.b64encode(result).decode('utf-8'),
            'isBase64Encoded': True
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### **2. Desplegar con SAM**
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    MemorySize: 3008
    Environment:
      Variables:
        OPENAI_API_KEY: !Ref OpenAIKey

Parameters:
  OpenAIKey:
    Type: String
    Description: OpenAI API Key

Resources:
  AsistenteFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_function.lambda_handler
      Runtime: python3.11
      Layers:
        - !Ref PyTorchLayer
      Events:
        ProcessAudio:
          Type: Api
          Properties:
            Path: /process
            Method: post

  PyTorchLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      CompatibleRuntimes:
        - python3.11
      Content:
        S3Bucket: your-layers-bucket
        S3Key: pytorch-layer.zip
```

### **3. Desplegar**
```bash
# Instalar AWS SAM
pip install aws-sam-cli

# Construir
sam build

# Desplegar
sam deploy --guided
```

---

## 📊 MONITOREO Y OPTIMIZACIÓN

### **Métricas a Monitorear**
```python
# Agregar a api.py
from fastapi.middleware.base import BaseHTTPMiddleware
import time

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        print(f"📊 {request.method} {request.url} - {response.status_code} - {process_time:.2f}s")

        return response

app.add_middleware(MetricsMiddleware)
```

### **Health Check Endpoint**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }
```

### **Configuración de CORS**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar para producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 RECOMENDACIONES FINALES

### **Para Desarrollo Rápido:**
```bash
# Vercel - Más fácil
vercel --prod
```

### **Para Producción Pequeña:**
```bash
# Heroku - Balance perfecto
git push heroku main
```

### **Para Escalado Empresarial:**
```bash
# Cloud Run - Mejor rendimiento
gcloud run deploy
```

### **Para Optimización Máxima:**
```bash
# AWS Lambda - Costo por uso
sam deploy
```

### **URLs de Producción Esperadas:**
- **Vercel:** `https://asistente-virtual.vercel.app/process`
- **Heroku:** `https://tu-app.herokuapp.com/process`
- **Cloud Run:** `https://asistente-service-hash-uc.a.run.app/process`
- **AWS:** `https://api-id.execute-api.region.amazonaws.com/prod/process`

---

**🎯 Elección Recomendada:**
- **Inicio:** Vercel (gratuito, rápido)
- **Crecimiento:** Heroku (fácil escalado)
- **Empresa:** Cloud Run (mejor rendimiento)