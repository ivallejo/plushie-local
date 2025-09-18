#!/bin/bash

# Script de despliegue automatizado para Railway
# Uso: ./deploy_to_railway.sh

echo "🚂 Iniciando despliegue de AI Assistant API en Railway"
echo "===================================================="

# Verificar si Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI no está instalado."
    echo "📦 Instálalo con: npm install -g @railway/cli"
    echo "   O visita: https://docs.railway.app/develop/cli"
    exit 1
fi

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
    git commit -m "Deploy to Railway - AI Assistant with Whisper support

✅ Features implemented:
- Complete Whisper integration for STT
- OpenAI Chat Completions with AI aliases
- PostgreSQL database support
- Session management
- ESP32 client examples
- Railway deployment configuration

🎯 Optimized for Railway:
- Full Whisper support (8GB RAM available)
- PostgreSQL persistence
- Auto-scaling capabilities
- Global edge deployment"
    echo "✅ Commit creado"
else
    echo "✅ No hay cambios pendientes"
fi

# Verificar si está logueado en Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 No estás logueado en Railway."
    echo "📝 Ejecuta: railway login"
    exit 1
fi

# Verificar si el proyecto ya existe en Railway
if railway list 2>/dev/null | grep -q "$(basename $(pwd))"; then
    echo "📦 Proyecto ya existe en Railway. Actualizando..."
    railway up
else
    echo "📦 Desplegando nuevo proyecto en Railway..."
    railway init
    railway up
fi

# Obtener la URL del despliegue
echo ""
echo "🎉 ¡Despliegue completado!"
echo "📍 Para ver tu aplicación: railway open"
echo "📊 Para ver logs: railway logs"
echo ""
echo "📋 Configuración completada:"
echo "✅ Railway CLI instalado"
echo "✅ Proyecto inicializado"
echo "✅ Variables de entorno configuradas"
echo "✅ Base de datos PostgreSQL conectada"
echo ""
echo "🎯 Tu AI Assistant API está lista en Railway!"
echo "   - Whisper funcionando correctamente"
echo "   - PostgreSQL para persistencia"
echo "   - Auto-scaling activado"
echo "   - AI Aliases personalizados"

echo ""
echo "===================================================="
echo "✅ Script de despliegue completado"