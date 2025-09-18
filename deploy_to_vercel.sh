#!/bin/bash

# Script de despliegue automatizado para Vercel
# Uso: ./deploy_to_vercel.sh

echo "🚀 Iniciando despliegue de AI Assistant API en Vercel"
echo "=================================================="

# Verificar si Vercel CLI está instalado
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI no está instalado."
    echo "📦 Instálalo con: npm install -g vercel"
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
    git commit -m "Deploy to Vercel - $(date)"
    echo "✅ Commit creado"
else
    echo "✅ No hay cambios pendientes"
fi

# Verificar si ya está logueado en Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 No estás logueado en Vercel."
    echo "📝 Ejecuta: vercel login"
    exit 1
fi

# Verificar si el proyecto ya existe en Vercel
if vercel ls 2>/dev/null | grep -q "$(basename $(pwd))"; then
    echo "📦 Proyecto ya existe en Vercel. Actualizando..."
    vercel --prod
else
    echo "📦 Desplegando nuevo proyecto en Vercel..."
    vercel --prod
fi

# Obtener la URL del despliegue
DEPLOY_URL=$(vercel --prod 2>&1 | grep -o 'https://[^ ]*\.vercel\.app')

if [[ -n "$DEPLOY_URL" ]]; then
    echo ""
    echo "🎉 ¡Despliegue exitoso!"
    echo "📍 URL de tu API: $DEPLOY_URL"
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Ve a $DEPLOY_URL para verificar que funciona"
    echo "2. Configura las variables de entorno en Vercel:"
    echo "   - OPENAI_API_KEY"
    echo "   - ASSISTANT_ID (opcional)"
    echo "3. Prueba los endpoints con el script test_vercel_api.py"
    echo ""
    echo "📖 Documentación completa en DEPLOYMENT_README.md"
else
    echo "❌ Error al obtener la URL del despliegue"
    echo "📝 Revisa los logs de Vercel para más detalles"
fi

echo ""
echo "=================================================="
echo "✅ Script de despliegue completado"