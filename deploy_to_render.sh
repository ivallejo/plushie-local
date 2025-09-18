#!/bin/bash

# Script de despliegue automatizado para Render
# Uso: ./deploy_to_render.sh

echo "🎨 Iniciando despliegue de AI Assistant API en Render"
echo "==================================================="

# Verificar si estamos en un repositorio git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ No estás en un repositorio git."
    echo "📝 Inicializa git: git init"
    exit 1
fi

# Verificar si hay cambios sin commitear
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Hay cambios sin commitear. Creando commit..."
    git add .
    git commit -m "Deploy to Render - AI Assistant with Whisper support

✅ Features implemented:
- Complete Whisper integration for STT
- OpenAI Chat Completions with AI aliases
- PostgreSQL database support
- Session management
- ESP32 client examples
- Render deployment configuration

🎯 Optimized for Render:
- 2GB RAM capacity utilized
- PostgreSQL persistence
- Auto-scaling capabilities
- Global edge deployment

📦 Files Added:
- render.yaml (Render config)
- deploy_to_render.sh (automated deployment)
- RENDER_DEPLOYMENT.md (complete guide)
- Updated requirements.txt (full dependencies)
- Updated .gitignore (Render specific)
- Restored api/__init__.py (complete Whisper integration)

🚀 Ready for Render deployment with full functionality!"
    echo "✅ Commit creado"
else
    echo "✅ No hay cambios pendientes"
fi

# Hacer push al repositorio
echo "📤 Subiendo cambios a GitHub..."
if git push origin main; then
    echo "✅ Push exitoso a GitHub"
else
    echo "❌ Error en push. Verifica tu conexión y credenciales"
    exit 1
fi

echo ""
echo "🎉 ¡Preparación completada!"
echo "📍 Siguientes pasos en Render:"
echo ""
echo "1. Ve a https://render.com"
echo "2. 'New' → 'Web Service'"
echo "3. Conecta tu repo: ivallejo/plushie-local"
echo "4. Configura:"
echo "   - Runtime: Python 3"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: python api/__init__.py"
echo "5. Variables de entorno:"
echo "   - OPENAI_API_KEY: tu_clave_de_openai"
echo "   - ASSISTANT_ID: tu_assistant_id (opcional)"
echo "6. 'Create Web Service'"
echo ""
echo "⏱️  Tiempo estimado: 5-10 minutos"
echo "📊 Monitorea el progreso en Render dashboard"
echo ""
echo "🎯 Tu AI Assistant estará listo en:"
echo "   https://tu-proyecto.onrender.com"
echo ""
echo "==================================================="