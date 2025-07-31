# Guía de Despliegue - GenAI-IaC Platform

## Descripción General

La plataforma GenAI-IaC es una solución completa para la gestión de infraestructura como código asistida por inteligencia artificial. Permite a los usuarios describir sus necesidades de infraestructura en lenguaje natural y generar automáticamente código Terraform validado y ejecutable.

## Arquitectura de la Plataforma

### Componentes Principales

1. **Frontend (React)**: Interfaz de usuario moderna y responsiva
2. **Backend (Flask)**: API REST para la lógica de negocio
3. **Base de Datos (SQLite)**: Almacenamiento de proyectos, prompts y configuraciones
4. **Integración LLM**: Soporte para múltiples proveedores (Gemini, OpenAI, Claude)
5. **Gestión de Estado**: Integración con S3/GCS para estado remoto de Terraform
6. **Control de Versiones**: Sincronización automática con repositorios Git

### Flujo de Trabajo

1. **Entrada de Prompt**: El usuario describe sus necesidades en lenguaje natural
2. **Procesamiento IA**: El LLM analiza el prompt y genera código Terraform
3. **Validación**: Se ejecuta `terraform plan` para validar el código
4. **Aprobación**: El usuario revisa y aprueba los cambios propuestos
5. **Ejecución**: Se aplican los cambios con `terraform apply`
6. **Sincronización**: Los cambios se sincronizan con Git automáticamente

## Requisitos del Sistema

### Requisitos Mínimos

- **Sistema Operativo**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+
- **Python**: 3.11+
- **Node.js**: 20.18+
- **Docker**: 20.10+
- **Memoria RAM**: 4GB mínimo, 8GB recomendado
- **Espacio en Disco**: 10GB mínimo

### Dependencias Externas

- **Docker**: Para la ejecución aislada de Terraform
- **Git**: Para el control de versiones
- **Acceso a Internet**: Para descargar dependencias y comunicarse con APIs

## Instalación y Configuración

### 1. Preparación del Entorno

```bash
# Clonar el repositorio
git clone <repository-url>
cd genai-iac-platform

# Verificar requisitos
python3.11 --version
node --version
docker --version
```

### 2. Configuración del Backend

```bash
# Navegar al directorio del backend
cd backend

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Configuración del Frontend

```bash
# Navegar al directorio del frontend
cd ../frontend

# Instalar dependencias
pnpm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tus configuraciones
```

### 4. Configuración de Docker

```bash
# Descargar imagen de Terraform
docker pull hashicorp/terraform:1.9

# Verificar que Docker esté funcionando
docker run --rm hashicorp/terraform:1.9 version
```

## Variables de Entorno

### Backend (.env)

```bash
# Configuración de la aplicación
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Base de datos
DATABASE_URL=sqlite:///app.db

# Configuración de CORS
CORS_ORIGINS=http://localhost:5173

# Configuración de Docker
DOCKER_TERRAFORM_IMAGE=hashicorp/terraform:1.9
```

### Frontend (.env.local)

```bash
# URL del backend
VITE_API_URL=http://localhost:5000/api

# Configuración de desarrollo
VITE_DEV_MODE=true
```

## Ejecución en Desarrollo

### 1. Iniciar el Backend

```bash
cd backend
source venv/bin/activate
python src/main.py
```

El backend estará disponible en `http://localhost:5000`

### 2. Iniciar el Frontend

```bash
cd frontend
pnpm run dev
```

El frontend estará disponible en `http://localhost:5173`

## Configuración de Proyectos

### 1. Crear un Nuevo Proyecto

1. Acceder a la sección "Proyectos" en la interfaz web
2. Hacer clic en "Nuevo Proyecto"
3. Completar la información básica:
   - Nombre del proyecto
   - Descripción
   - Proveedor de nube (AWS/Azure/GCP)

### 2. Configurar LLM

En la pestaña "LLM":
- Seleccionar el proveedor (Gemini, OpenAI, Claude)
- Ingresar la API key correspondiente
- Opcionalmente, personalizar el system prompt

### 3. Configurar Estado Remoto

En la pestaña "Estado":
- Ingresar la URL del bucket (s3://bucket-name o gs://bucket-name)
- Configurar las credenciales necesarias

### 4. Configurar Git (Opcional)

En la pestaña "Git":
- Ingresar la URL del repositorio
- Configurar clave SSH si es necesario

## Uso de la Plataforma

### 1. Envío de Prompts

1. Seleccionar un proyecto configurado
2. Escribir la descripción de la infraestructura deseada
3. Hacer clic en "Enviar Prompt"

Ejemplo de prompt:
```
Crear una aplicación web escalable en AWS con:
- Load balancer público
- 2 instancias EC2 en subnets privadas
- Base de datos RDS PostgreSQL
- Bucket S3 para archivos estáticos
```

### 2. Revisión y Aprobación

1. Revisar el código Terraform generado
2. Examinar el plan de ejecución
3. Aprobar o rechazar los cambios

### 3. Ejecución

1. Confirmar la aplicación de cambios
2. Monitorear el progreso de la ejecución
3. Revisar los resultados

## Despliegue en Producción

### Usando Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/genai_iac
    volumes:
      - ./data:/app/data
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=genai_iac
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Configuración de Nginx (Opcional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Seguridad

### Recomendaciones de Seguridad

1. **API Keys**: Nunca hardcodear API keys en el código
2. **HTTPS**: Usar HTTPS en producción
3. **Autenticación**: Implementar autenticación de usuarios
4. **Firewall**: Configurar firewall para limitar acceso
5. **Backups**: Realizar backups regulares de la base de datos

### Variables Sensibles

- API keys de LLM
- Credenciales de AWS/GCP
- Claves SSH para Git
- Secret key de Flask

## Monitoreo y Logs

### Logs del Backend

Los logs se almacenan en:
- Desarrollo: Consola
- Producción: `/var/log/genai-iac/backend.log`

### Logs del Frontend

Los logs del navegador están disponibles en las herramientas de desarrollador.

### Métricas Recomendadas

- Tiempo de respuesta de APIs
- Uso de recursos (CPU, memoria)
- Errores de ejecución de Terraform
- Tasa de éxito de prompts

## Solución de Problemas

### Problemas Comunes

1. **Error de conexión con LLM**
   - Verificar API key
   - Comprobar conectividad a internet
   - Revisar límites de rate limiting

2. **Fallo en ejecución de Terraform**
   - Verificar credenciales de cloud provider
   - Comprobar permisos IAM
   - Revisar sintaxis del código generado

3. **Error de sincronización con Git**
   - Verificar URL del repositorio
   - Comprobar clave SSH
   - Revisar permisos del repositorio

### Comandos de Diagnóstico

```bash
# Verificar estado de Docker
docker ps
docker logs <container-id>

# Verificar conectividad
curl -I http://localhost:5000/api/health
curl -I http://localhost:5173

# Verificar logs del backend
tail -f backend/logs/app.log

# Verificar base de datos
sqlite3 backend/src/database/app.db ".tables"
```

## Mantenimiento

### Actualizaciones

1. **Dependencias de Python**:
   ```bash
   pip list --outdated
   pip install -U package-name
   ```

2. **Dependencias de Node.js**:
   ```bash
   pnpm outdated
   pnpm update
   ```

3. **Imagen de Terraform**:
   ```bash
   docker pull hashicorp/terraform:latest
   ```

### Backups

```bash
# Backup de base de datos
cp backend/src/database/app.db backups/app_$(date +%Y%m%d).db

# Backup de configuraciones
tar -czf backups/config_$(date +%Y%m%d).tar.gz backend/.env frontend/.env.local
```

## Soporte

Para obtener soporte:

1. Revisar esta documentación
2. Consultar los logs de error
3. Verificar la configuración
4. Contactar al equipo de desarrollo

## Licencia

Este proyecto está licenciado bajo [especificar licencia].

