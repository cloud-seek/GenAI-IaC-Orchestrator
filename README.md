# GenAI-IaC Platform

## 🚀 Plataforma de Gestión de Infraestructura como Código Asistida por IA

GenAI-IaC Platform es una solución innovadora que permite a los usuarios describir sus necesidades de infraestructura en lenguaje natural y generar automáticamente código Terraform validado y ejecutable. La plataforma integra inteligencia artificial avanzada con las mejores prácticas de DevOps para simplificar la gestión de infraestructura en la nube.

## ✨ Características Principales

### 🤖 Interfaz Basada en Prompts
- **Lenguaje Natural**: Describe tu infraestructura en español o inglés
- **IA Avanzada**: Integración con múltiples proveedores de LLM (Gemini, OpenAI, Claude)
- **Generación Inteligente**: Código Terraform optimizado y siguiendo mejores prácticas

### 🏗️ Gestión Completa de Terraform
- **Validación Automática**: Verificación de sintaxis y lógica del código generado
- **Ejecución Controlada**: Plan, apply y destroy con aprobación manual
- **Contenedores Docker**: Ejecución aislada y segura de Terraform

### 🌐 Soporte Multi-Cloud
- **AWS**: Amazon Web Services
- **Azure**: Microsoft Azure
- **GCP**: Google Cloud Platform

### 📊 Visualización de Infraestructura
- **Inventario de Recursos**: Vista detallada de todos los recursos desplegados
- **Estado en Tiempo Real**: Monitoreo del estado de la infraestructura
- **Filtros Avanzados**: Búsqueda y filtrado por tipo, estado y etiquetas

### 🔄 Integración con Git
- **Sincronización Automática**: Código Terraform versionado en repositorios Git
- **Control de Versiones**: Historial completo de cambios
- **Colaboración**: Trabajo en equipo con flujos de Git estándar

### 🗄️ Gestión de Estado Centralizada
- **Backends Remotos**: Soporte para S3, GCS y otros backends
- **Estado Compartido**: Colaboración segura entre equipos
- **Bloqueo de Estado**: Prevención de conflictos concurrentes

### 🏢 Multi-Tenant
- **Proyectos Aislados**: Gestión independiente de múltiples proyectos
- **Configuración Personalizada**: LLM, estado y Git por proyecto
- **Seguridad**: Aislamiento completo entre proyectos

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Servicios     │
│   (React)       │◄──►│   (Flask)       │◄──►│   Externos      │
│                 │    │                 │    │                 │
│ • Interfaz Web  │    │ • API REST      │    │ • LLM APIs      │
│ • Gestión UI    │    │ • Lógica        │    │ • Git Repos     │
│ • Visualización │    │ • Validación    │    │ • Cloud APIs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Terraform     │
                       │   (Docker)      │
                       │                 │
                       │ • Plan/Apply    │
                       │ • Validación    │
                       │ • Estado        │
                       └─────────────────┘
```

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.11+
- Node.js 20.18+
- Docker 20.10+
- Git

### Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd genai-iac-platform
   ```

2. **Configurar el backend**:
   ```bash
   cd backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configurar el frontend**:
   ```bash
   cd ../frontend
   pnpm install
   ```

4. **Configurar Docker**:
   ```bash
   docker pull hashicorp/terraform:1.9
   ```

### Ejecución

1. **Iniciar el backend**:
   ```bash
   cd backend
   source venv/bin/activate
   python src/main.py
   ```

2. **Iniciar el frontend**:
   ```bash
   cd frontend
   pnpm run dev
   ```

3. **Acceder a la aplicación**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000

## 📖 Documentación

- **[Guía de Despliegue](DEPLOYMENT_GUIDE.md)**: Instalación y configuración detallada
- **[Documentación de API](API_DOCUMENTATION.md)**: Referencia completa de la API REST
- **[Ejemplos de Uso](examples/)**: Casos de uso y ejemplos prácticos

## 🎯 Casos de Uso

### 1. Desarrollo Rápido de Prototipos
```
Prompt: "Crear un entorno de desarrollo con una instancia EC2, base de datos RDS y bucket S3"
```

### 2. Aplicaciones Web Escalables
```
Prompt: "Desplegar una aplicación web con load balancer, auto scaling group de 2-10 instancias, base de datos PostgreSQL y CDN"
```

### 3. Infraestructura de Microservicios
```
Prompt: "Crear un cluster EKS con 3 nodos, ALB ingress controller, y base de datos Aurora para microservicios"
```

### 4. Entorno de CI/CD
```
Prompt: "Configurar pipeline de CI/CD con CodeBuild, CodePipeline, ECR y despliegue en ECS"
```

## 🔧 Configuración

### Variables de Entorno

**Backend (.env)**:
```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
CORS_ORIGINS=http://localhost:5173
```

**Frontend (.env.local)**:
```bash
VITE_API_URL=http://localhost:5000/api
VITE_DEV_MODE=true
```

### Configuración de Proyectos

1. **Crear Proyecto**: Definir nombre, descripción y proveedor de nube
2. **Configurar LLM**: Seleccionar proveedor y API key
3. **Configurar Estado**: Definir backend remoto (S3/GCS)
4. **Configurar Git**: Opcional, para versionado automático

## 🛠️ Desarrollo

### Estructura del Proyecto

```
genai-iac-platform/
├── backend/                 # API Flask
│   ├── src/
│   │   ├── main.py         # Punto de entrada
│   │   ├── models/         # Modelos de datos
│   │   ├── routes/         # Endpoints de API
│   │   └── services/       # Lógica de negocio
│   └── requirements.txt
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── pages/          # Páginas principales
│   │   └── utils/          # Utilidades
│   └── package.json
├── docs/                   # Documentación
├── examples/               # Ejemplos de uso
└── README.md
```

### Tecnologías Utilizadas

**Backend**:
- Flask (Framework web)
- LiteLLM (Integración con LLMs)
- Docker (Contenedores)
- SQLite (Base de datos)

**Frontend**:
- React 18 (Framework UI)
- Vite (Build tool)
- Tailwind CSS (Estilos)
- Shadcn/ui (Componentes)

## 🧪 Pruebas

### Pruebas del Backend
```bash
cd backend
python -m pytest tests/
```

### Pruebas del Frontend
```bash
cd frontend
pnpm test
```

### Pruebas de Integración
```bash
# Ejecutar ambos servidores y probar endpoints
curl http://localhost:5000/api/health
```

## 🚀 Despliegue

### Docker Compose
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

### Cloud Providers
- AWS: ECS/EKS
- Azure: Container Instances/AKS
- GCP: Cloud Run/GKE

## 🔒 Seguridad

- **API Keys**: Almacenamiento seguro de credenciales
- **Validación**: Sanitización de inputs y código generado
- **Aislamiento**: Ejecución de Terraform en contenedores
- **Auditoría**: Logs completos de todas las operaciones

## 🤝 Contribución

1. Fork el repositorio
2. Crear una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## 📝 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

- **Issues**: [GitHub Issues](https://github.com/user/genai-iac-platform/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/user/genai-iac-platform/wiki)
- **Discusiones**: [GitHub Discussions](https://github.com/user/genai-iac-platform/discussions)

## 🗺️ Roadmap

### v1.1.0 (Q2 2025)
- [ ] Autenticación y autorización
- [ ] Métricas y monitoreo
- [ ] Plantillas de infraestructura

### v1.2.0 (Q3 2025)
- [ ] Soporte para Ansible
- [ ] Integración con Kubernetes
- [ ] Dashboard de costos

### v2.0.0 (Q4 2025)
- [ ] Soporte multi-cloud simultáneo
- [ ] IA para optimización de costos
- [ ] Marketplace de plantillas

## 🏆 Reconocimientos

- Equipo de desarrollo de GenAI-IaC Platform
- Comunidad open source de Terraform
- Proveedores de LLM (Google, OpenAI, Anthropic)

---

**¡Transforma tu gestión de infraestructura con el poder de la IA!** 🚀

