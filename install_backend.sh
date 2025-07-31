#!/bin/bash

# Script de instalación rápida para el backend de GenAI-IaC Platform

# Ir al directorio del backend
cd backend

echo "Creando entorno virtual de Python..."
python3.11 -m venv venv

echo "Activando entorno virtual e instalando dependencias..."
source venv/bin/activate
pip install -r requirements.txt

echo "Instalación del backend completada. Para activar el entorno virtual, ejecuta: source venv/bin/activate"


