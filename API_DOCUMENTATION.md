# Documentación de API - GenAI-IaC Platform

## Descripción General

La API de GenAI-IaC Platform proporciona endpoints RESTful para gestionar proyectos de infraestructura como código, procesar prompts de lenguaje natural y ejecutar operaciones de Terraform.

**Base URL**: `http://localhost:5000/api`

## Autenticación

Actualmente la API no requiere autenticación. En futuras versiones se implementará autenticación basada en tokens JWT.

## Endpoints

### Proyectos

#### GET /projects
Obtiene la lista de todos los proyectos.

**Respuesta**:
```json
[
  {
    "id": 1,
    "name": "mi-proyecto-aws",
    "description": "Proyecto de infraestructura en AWS",
    "cloud_provider": "aws",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:22:00Z"
  }
]
```

#### POST /projects
Crea un nuevo proyecto.

**Cuerpo de la solicitud**:
```json
{
  "name": "nuevo-proyecto",
  "description": "Descripción del proyecto",
  "cloud_provider": "aws",
  "llm_provider": "gemini",
  "llm_api_key": "api-key-here",
  "system_prompt": "Prompt personalizado opcional",
  "state_backend": {
    "type": "s3",
    "bucket": "mi-bucket-terraform",
    "region": "us-east-1"
  },
  "git_config": {
    "repository_url": "git@github.com:user/repo.git",
    "branch": "main"
  }
}
```

**Respuesta**:
```json
{
  "id": 2,
  "name": "nuevo-proyecto",
  "description": "Descripción del proyecto",
  "cloud_provider": "aws",
  "created_at": "2024-01-21T09:15:00Z"
}
```

#### GET /projects/{id}
Obtiene los detalles de un proyecto específico.

**Respuesta**:
```json
{
  "id": 1,
  "name": "mi-proyecto-aws",
  "description": "Proyecto de infraestructura en AWS",
  "cloud_provider": "aws",
  "llm_provider": "gemini",
  "state_backend": {
    "type": "s3",
    "bucket": "mi-bucket-terraform",
    "region": "us-east-1"
  },
  "git_config": {
    "repository_url": "git@github.com:user/repo.git",
    "branch": "main"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:22:00Z"
}
```

#### PUT /projects/{id}
Actualiza un proyecto existente.

**Cuerpo de la solicitud**: Igual que POST /projects

#### DELETE /projects/{id}
Elimina un proyecto.

**Respuesta**: 204 No Content

### Prompts

#### POST /prompts/process
Procesa un prompt de lenguaje natural y genera código Terraform.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "prompt": "Crear una aplicación web con load balancer y 2 instancias EC2",
  "context": "Información adicional opcional"
}
```

**Respuesta**:
```json
{
  "id": "prompt-123",
  "status": "processing",
  "terraform_code": null,
  "plan_output": null,
  "created_at": "2024-01-21T10:00:00Z"
}
```

#### GET /prompts/{id}
Obtiene el estado y resultado de un prompt procesado.

**Respuesta**:
```json
{
  "id": "prompt-123",
  "status": "completed",
  "terraform_code": "resource \"aws_instance\" \"web\" {\n  ami = \"ami-12345\"\n  instance_type = \"t3.micro\"\n}",
  "plan_output": "Plan: 3 to add, 0 to change, 0 to destroy.",
  "validation_errors": [],
  "created_at": "2024-01-21T10:00:00Z",
  "completed_at": "2024-01-21T10:02:30Z"
}
```

### LLM

#### POST /llm/generate
Genera código Terraform usando el LLM configurado.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "prompt": "Crear una base de datos PostgreSQL en AWS RDS",
  "provider": "gemini",
  "model": "gemini-pro"
}
```

**Respuesta**:
```json
{
  "generated_code": "resource \"aws_db_instance\" \"postgres\" {\n  engine = \"postgres\"\n  instance_class = \"db.t3.micro\"\n}",
  "explanation": "Este código crea una instancia de base de datos PostgreSQL...",
  "tokens_used": 150
}
```

#### POST /llm/validate
Valida y mejora código Terraform existente.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "terraform_code": "resource \"aws_instance\" \"web\" { ami = \"ami-12345\" }",
  "validation_type": "syntax"
}
```

**Respuesta**:
```json
{
  "is_valid": false,
  "errors": [
    {
      "line": 1,
      "message": "Missing required argument: instance_type"
    }
  ],
  "suggestions": [
    "Agregar instance_type = \"t3.micro\""
  ],
  "improved_code": "resource \"aws_instance\" \"web\" {\n  ami = \"ami-12345\"\n  instance_type = \"t3.micro\"\n}"
}
```

### Terraform

#### POST /terraform/plan
Ejecuta `terraform plan` para un proyecto.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "terraform_code": "resource \"aws_instance\" \"web\" {\n  ami = \"ami-12345\"\n  instance_type = \"t3.micro\"\n}"
}
```

**Respuesta**:
```json
{
  "execution_id": "exec-456",
  "status": "running",
  "plan_output": null,
  "started_at": "2024-01-21T11:00:00Z"
}
```

#### POST /terraform/apply
Ejecuta `terraform apply` para aplicar cambios.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "execution_id": "exec-456",
  "auto_approve": false
}
```

**Respuesta**:
```json
{
  "execution_id": "exec-789",
  "status": "running",
  "apply_output": null,
  "started_at": "2024-01-21T11:05:00Z"
}
```

#### GET /terraform/executions/{id}
Obtiene el estado de una ejecución de Terraform.

**Respuesta**:
```json
{
  "execution_id": "exec-456",
  "status": "completed",
  "command": "plan",
  "output": "Plan: 1 to add, 0 to change, 0 to destroy.",
  "exit_code": 0,
  "started_at": "2024-01-21T11:00:00Z",
  "completed_at": "2024-01-21T11:01:15Z"
}
```

#### POST /terraform/destroy
Ejecuta `terraform destroy` para eliminar recursos.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "auto_approve": false
}
```

### Estado

#### GET /state/backends
Obtiene los backends de estado disponibles.

**Respuesta**:
```json
[
  {
    "type": "s3",
    "name": "Amazon S3",
    "required_fields": ["bucket", "region", "key"]
  },
  {
    "type": "gcs",
    "name": "Google Cloud Storage",
    "required_fields": ["bucket", "prefix"]
  }
]
```

#### POST /state/configure
Configura el backend de estado para un proyecto.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "backend_type": "s3",
  "config": {
    "bucket": "mi-bucket-terraform",
    "key": "terraform.tfstate",
    "region": "us-east-1"
  }
}
```

#### GET /state/status/{project_id}
Obtiene el estado actual del backend de estado.

**Respuesta**:
```json
{
  "project_id": 1,
  "backend_configured": true,
  "last_modified": "2024-01-21T10:30:00Z",
  "state_version": 4,
  "resources_count": 5
}
```

### Git

#### POST /git/sync
Sincroniza el código Terraform con el repositorio Git.

**Cuerpo de la solicitud**:
```json
{
  "project_id": 1,
  "commit_message": "Actualizar infraestructura con nuevos recursos",
  "branch": "main"
}
```

**Respuesta**:
```json
{
  "sync_id": "sync-123",
  "status": "running",
  "commit_hash": null,
  "started_at": "2024-01-21T12:00:00Z"
}
```

#### GET /git/status/{project_id}
Obtiene el estado de sincronización con Git.

**Respuesta**:
```json
{
  "project_id": 1,
  "repository_url": "git@github.com:user/repo.git",
  "current_branch": "main",
  "last_commit": "abc123def456",
  "last_sync": "2024-01-21T11:45:00Z",
  "pending_changes": false
}
```

### Recursos

#### GET /projects/{id}/resources
Obtiene el inventario de recursos de un proyecto.

**Respuesta**:
```json
[
  {
    "id": 1,
    "name": "web-server-01",
    "type": "aws_instance",
    "provider": "aws",
    "status": "running",
    "region": "us-east-1",
    "attributes": {
      "instance_type": "t3.medium",
      "ami": "ami-0abcdef1234567890",
      "public_ip": "54.123.45.67"
    },
    "tags": {
      "Environment": "production",
      "Application": "web-frontend"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "last_modified": "2024-01-20T14:22:00Z"
  }
]
```

#### GET /resources/{id}
Obtiene los detalles de un recurso específico.

**Respuesta**:
```json
{
  "id": 1,
  "name": "web-server-01",
  "type": "aws_instance",
  "provider": "aws",
  "status": "running",
  "region": "us-east-1",
  "attributes": {
    "instance_type": "t3.medium",
    "ami": "ami-0abcdef1234567890",
    "vpc_id": "vpc-12345678",
    "subnet_id": "subnet-87654321",
    "security_groups": ["sg-web-servers"],
    "public_ip": "54.123.45.67",
    "private_ip": "10.0.1.100"
  },
  "tags": {
    "Environment": "production",
    "Application": "web-frontend",
    "Owner": "devops-team"
  },
  "dependencies": [
    {
      "resource_id": 2,
      "resource_name": "vpc-main",
      "dependency_type": "vpc"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "last_modified": "2024-01-20T14:22:00Z"
}
```

## Códigos de Estado HTTP

- **200 OK**: Solicitud exitosa
- **201 Created**: Recurso creado exitosamente
- **204 No Content**: Operación exitosa sin contenido de respuesta
- **400 Bad Request**: Error en la solicitud del cliente
- **401 Unauthorized**: Autenticación requerida
- **403 Forbidden**: Acceso denegado
- **404 Not Found**: Recurso no encontrado
- **409 Conflict**: Conflicto con el estado actual del recurso
- **422 Unprocessable Entity**: Error de validación
- **500 Internal Server Error**: Error interno del servidor

## Manejo de Errores

Todas las respuestas de error siguen el siguiente formato:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos proporcionados no son válidos",
    "details": [
      {
        "field": "name",
        "message": "El nombre es requerido"
      }
    ]
  }
}
```

### Códigos de Error Comunes

- **VALIDATION_ERROR**: Error de validación de datos
- **PROJECT_NOT_FOUND**: Proyecto no encontrado
- **LLM_API_ERROR**: Error en la API del LLM
- **TERRAFORM_EXECUTION_ERROR**: Error en la ejecución de Terraform
- **GIT_SYNC_ERROR**: Error en la sincronización con Git
- **STATE_BACKEND_ERROR**: Error en el backend de estado

## Rate Limiting

La API implementa rate limiting para prevenir abuso:

- **Límite general**: 100 solicitudes por minuto por IP
- **Límite de LLM**: 10 solicitudes por minuto por proyecto
- **Límite de Terraform**: 5 ejecuciones por minuto por proyecto

Los headers de respuesta incluyen información sobre el rate limiting:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642781400
```

## Webhooks

La plataforma puede enviar webhooks para notificar eventos importantes:

### Eventos Disponibles

- **project.created**: Proyecto creado
- **prompt.completed**: Prompt procesado
- **terraform.plan.completed**: Plan de Terraform completado
- **terraform.apply.completed**: Apply de Terraform completado
- **git.sync.completed**: Sincronización con Git completada

### Formato del Webhook

```json
{
  "event": "terraform.apply.completed",
  "timestamp": "2024-01-21T12:00:00Z",
  "data": {
    "project_id": 1,
    "execution_id": "exec-789",
    "status": "success",
    "resources_created": 3,
    "resources_modified": 0,
    "resources_destroyed": 0
  }
}
```

## Ejemplos de Uso

### Flujo Completo de Creación de Infraestructura

```bash
# 1. Crear un proyecto
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mi-app-web",
    "description": "Aplicación web escalable",
    "cloud_provider": "aws",
    "llm_provider": "gemini",
    "llm_api_key": "your-api-key"
  }'

# 2. Procesar un prompt
curl -X POST http://localhost:5000/api/prompts/process \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "prompt": "Crear una aplicación web con load balancer y 2 instancias EC2"
  }'

# 3. Verificar el resultado
curl http://localhost:5000/api/prompts/prompt-123

# 4. Ejecutar plan de Terraform
curl -X POST http://localhost:5000/api/terraform/plan \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "terraform_code": "..."
  }'

# 5. Aplicar cambios
curl -X POST http://localhost:5000/api/terraform/apply \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "execution_id": "exec-456",
    "auto_approve": true
  }'
```

## SDK y Librerías Cliente

### Python SDK (Ejemplo)

```python
from genai_iac_client import GenAIIaCClient

client = GenAIIaCClient(base_url="http://localhost:5000/api")

# Crear proyecto
project = client.projects.create(
    name="mi-proyecto",
    description="Proyecto de prueba",
    cloud_provider="aws"
)

# Procesar prompt
result = client.prompts.process(
    project_id=project.id,
    prompt="Crear una base de datos PostgreSQL"
)

# Ejecutar plan
plan = client.terraform.plan(
    project_id=project.id,
    terraform_code=result.terraform_code
)
```

### JavaScript SDK (Ejemplo)

```javascript
import { GenAIIaCClient } from 'genai-iac-client';

const client = new GenAIIaCClient({
  baseURL: 'http://localhost:5000/api'
});

// Crear proyecto
const project = await client.projects.create({
  name: 'mi-proyecto',
  description: 'Proyecto de prueba',
  cloudProvider: 'aws'
});

// Procesar prompt
const result = await client.prompts.process({
  projectId: project.id,
  prompt: 'Crear una base de datos PostgreSQL'
});
```

## Versionado de API

La API utiliza versionado semántico. La versión actual es v1.

- **URL con versión**: `http://localhost:5000/api/v1/projects`
- **Header de versión**: `API-Version: v1`

## Changelog

### v1.0.0 (2024-01-21)
- Lanzamiento inicial de la API
- Soporte para proyectos, prompts, Terraform, Git y estado
- Integración con múltiples proveedores de LLM
- Inventario de recursos

### Próximas Versiones

- **v1.1.0**: Autenticación y autorización
- **v1.2.0**: Métricas y monitoreo
- **v1.3.0**: Plantillas de infraestructura
- **v2.0.0**: Soporte para múltiples clouds simultáneamente

