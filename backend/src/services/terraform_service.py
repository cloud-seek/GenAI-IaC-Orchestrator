import os
import json
import tempfile
import shutil
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.models.project import Project, TerraformPlan, Resource, db

class TerraformService:
    """Servicio para la gestión de Terraform en contenedores Docker"""
    
    def __init__(self):
        self.terraform_image = "hashicorp/terraform:1.9"
        self.work_dir = "/terraform"
    
    def create_terraform_workspace(self, project: Project, terraform_code: str) -> str:
        """
        Crea un workspace temporal con el código Terraform
        
        Returns:
            str: Ruta del directorio temporal creado
        """
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp(prefix=f"terraform_{project.name}_")
        
        # Escribir el código Terraform
        main_tf_path = os.path.join(temp_dir, "main.tf")
        with open(main_tf_path, 'w') as f:
            f.write(terraform_code)
        
        # Crear archivo de configuración del backend si está configurado
        if project.state_bucket_url:
            backend_config = self._generate_backend_config(project)
            backend_tf_path = os.path.join(temp_dir, "backend.tf")
            with open(backend_tf_path, 'w') as f:
                f.write(backend_config)
        
        # Crear archivo de variables si es necesario
        variables_tf_path = os.path.join(temp_dir, "variables.tf")
        with open(variables_tf_path, 'w') as f:
            f.write(self._generate_variables_config(project))
        
        return temp_dir
    
    def _generate_backend_config(self, project: Project) -> str:
        """Genera la configuración del backend para el estado remoto"""
        if not project.state_bucket_url:
            return ""
        
        # Determinar el tipo de backend basado en la URL
        if 's3://' in project.state_bucket_url:
            # Backend S3
            bucket_name = project.state_bucket_url.replace('s3://', '').split('/')[0]
            key = f"{project.name}/terraform.tfstate"
            
            return f"""
terraform {{
  backend "s3" {{
    bucket = "{bucket_name}"
    key    = "{key}"
    region = "us-east-1"  # Configurar según el proyecto
  }}
}}
"""
        elif 'gs://' in project.state_bucket_url:
            # Backend GCS
            bucket_name = project.state_bucket_url.replace('gs://', '').split('/')[0]
            prefix = f"{project.name}"
            
            return f"""
terraform {{
  backend "gcs" {{
    bucket = "{bucket_name}"
    prefix = "{prefix}"
  }}
}}
"""
        
        return ""
    
    def _generate_variables_config(self, project: Project) -> str:
        """Genera configuración de variables comunes"""
        return f"""
variable "project_name" {{
  description = "Nombre del proyecto"
  type        = string
  default     = "{project.name}"
}}

variable "environment" {{
  description = "Entorno de despliegue"
  type        = string
  default     = "dev"
}}

variable "cloud_provider" {{
  description = "Proveedor de nube"
  type        = string
  default     = "{project.cloud_provider}"
}}
"""
    
    def run_terraform_command(self, workspace_dir: str, command: List[str], project: Project) -> Dict[str, Any]:
        """
        Ejecuta un comando de Terraform en un contenedor Docker
        
        Args:
            workspace_dir: Directorio con los archivos de Terraform
            command: Comando de Terraform a ejecutar (ej: ['plan', '-out=plan.out'])
            project: Proyecto asociado
            
        Returns:
            Dict con el resultado de la ejecución
        """
        try:
            # Preparar el comando Docker
            docker_cmd = [
                'docker', 'run', '--rm',
                '-v', f'{workspace_dir}:{self.work_dir}',
                '-w', self.work_dir,
                '--user', f'{os.getuid()}:{os.getgid()}'
            ]
            
            # Agregar variables de entorno para credenciales
            env_vars = self._get_terraform_env_vars(project)
            for key, value in env_vars.items():
                docker_cmd.extend(['-e', f'{key}={value}'])
            
            # Agregar imagen y comando
            docker_cmd.append(self.terraform_image)
            docker_cmd.extend(command)
            
            # Ejecutar el comando
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos de timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'command': ' '.join(command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Comando de Terraform excedió el tiempo límite',
                'return_code': -1,
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'command': ' '.join(command)
            }
    
    def _get_terraform_env_vars(self, project: Project) -> Dict[str, str]:
        """Obtiene las variables de entorno necesarias para Terraform"""
        env_vars = {}
        
        # Variables según el proveedor de nube
        if project.cloud_provider.lower() == 'aws':
            # Para AWS, se necesitarían AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY
            # Por ahora, usar variables de entorno del sistema si están disponibles
            if 'AWS_ACCESS_KEY_ID' in os.environ:
                env_vars['AWS_ACCESS_KEY_ID'] = os.environ['AWS_ACCESS_KEY_ID']
            if 'AWS_SECRET_ACCESS_KEY' in os.environ:
                env_vars['AWS_SECRET_ACCESS_KEY'] = os.environ['AWS_SECRET_ACCESS_KEY']
            if 'AWS_DEFAULT_REGION' in os.environ:
                env_vars['AWS_DEFAULT_REGION'] = os.environ['AWS_DEFAULT_REGION']
        
        elif project.cloud_provider.lower() == 'gcp':
            # Para GCP, se necesitaría GOOGLE_APPLICATION_CREDENTIALS
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                env_vars['GOOGLE_APPLICATION_CREDENTIALS'] = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        
        elif project.cloud_provider.lower() == 'azure':
            # Para Azure, se necesitarían las credenciales de Azure
            azure_vars = ['ARM_CLIENT_ID', 'ARM_CLIENT_SECRET', 'ARM_SUBSCRIPTION_ID', 'ARM_TENANT_ID']
            for var in azure_vars:
                if var in os.environ:
                    env_vars[var] = os.environ[var]
        
        return env_vars
    
    def terraform_init(self, workspace_dir: str, project: Project) -> Dict[str, Any]:
        """Ejecuta terraform init"""
        return self.run_terraform_command(workspace_dir, ['init'], project)
    
    def terraform_plan(self, workspace_dir: str, project: Project, prompt_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Ejecuta terraform plan y guarda el resultado en la base de datos
        
        Returns:
            Dict con el resultado del plan y el ID del plan creado
        """
        # Ejecutar terraform init primero
        init_result = self.terraform_init(workspace_dir, project)
        if not init_result['success']:
            return {
                'success': False,
                'error': f"Error en terraform init: {init_result['stderr']}",
                'plan_id': None
            }
        
        # Ejecutar terraform plan
        plan_result = self.run_terraform_command(
            workspace_dir, 
            ['plan', '-out=plan.out', '-detailed-exitcode'], 
            project
        )
        
        # Obtener el plan en formato JSON
        json_result = self.run_terraform_command(
            workspace_dir,
            ['show', '-json', 'plan.out'],
            project
        )
        
        # Crear registro del plan en la base de datos
        terraform_plan = TerraformPlan(
            project_id=project.id,
            prompt_id=prompt_id,
            plan_output=plan_result['stdout'],
            plan_json=json_result['stdout'] if json_result['success'] else None,
            status='pending'
        )
        
        db.session.add(terraform_plan)
        db.session.commit()
        
        return {
            'success': plan_result['success'],
            'plan_id': terraform_plan.id,
            'plan_output': plan_result['stdout'],
            'plan_json': json_result['stdout'] if json_result['success'] else None,
            'has_changes': plan_result['return_code'] == 2,  # Exit code 2 significa que hay cambios
            'error': plan_result['stderr'] if not plan_result['success'] else None
        }
    
    def terraform_apply(self, workspace_dir: str, project: Project, plan_id: int) -> Dict[str, Any]:
        """
        Ejecuta terraform apply usando un plan previamente generado
        """
        try:
            # Obtener el plan de la base de datos
            terraform_plan = TerraformPlan.query.get(plan_id)
            if not terraform_plan or terraform_plan.project_id != project.id:
                return {
                    'success': False,
                    'error': 'Plan no encontrado o no pertenece al proyecto'
                }
            
            if terraform_plan.status != 'approved':
                return {
                    'success': False,
                    'error': 'El plan no ha sido aprobado'
                }
            
            # Ejecutar terraform apply
            apply_result = self.run_terraform_command(
                workspace_dir,
                ['apply', 'plan.out'],
                project
            )
            
            # Actualizar el estado del plan
            if apply_result['success']:
                terraform_plan.status = 'applied'
                terraform_plan.applied_at = datetime.utcnow()
                
                # Actualizar inventario de recursos
                self._update_resource_inventory(project)
            else:
                terraform_plan.status = 'failed'
            
            db.session.commit()
            
            return {
                'success': apply_result['success'],
                'output': apply_result['stdout'],
                'error': apply_result['stderr'] if not apply_result['success'] else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def terraform_destroy(self, workspace_dir: str, project: Project) -> Dict[str, Any]:
        """Ejecuta terraform destroy"""
        # Ejecutar terraform init primero
        init_result = self.terraform_init(workspace_dir, project)
        if not init_result['success']:
            return {
                'success': False,
                'error': f"Error en terraform init: {init_result['stderr']}"
            }
        
        # Ejecutar terraform destroy
        destroy_result = self.run_terraform_command(
            workspace_dir,
            ['destroy', '-auto-approve'],
            project
        )
        
        if destroy_result['success']:
            # Limpiar inventario de recursos
            Resource.query.filter_by(project_id=project.id).delete()
            db.session.commit()
        
        return {
            'success': destroy_result['success'],
            'output': destroy_result['stdout'],
            'error': destroy_result['stderr'] if not destroy_result['success'] else None
        }
    
    def _update_resource_inventory(self, project: Project):
        """Actualiza el inventario de recursos desde el estado de Terraform"""
        try:
            # Por ahora, implementación básica
            # En una implementación completa, se leería el estado de Terraform
            # y se actualizaría la tabla de recursos
            pass
        except Exception as e:
            print(f"Error actualizando inventario de recursos: {e}")
    
    def get_terraform_state(self, workspace_dir: str, project: Project) -> Dict[str, Any]:
        """Obtiene el estado actual de Terraform"""
        # Ejecutar terraform show para obtener el estado
        state_result = self.run_terraform_command(
            workspace_dir,
            ['show', '-json'],
            project
        )
        
        if state_result['success']:
            try:
                state_data = json.loads(state_result['stdout'])
                return {
                    'success': True,
                    'state': state_data
                }
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': 'Error parsing Terraform state JSON'
                }
        else:
            return {
                'success': False,
                'error': state_result['stderr']
            }
    
    def cleanup_workspace(self, workspace_dir: str):
        """Limpia el workspace temporal"""
        try:
            if os.path.exists(workspace_dir):
                shutil.rmtree(workspace_dir)
        except Exception as e:
            print(f"Error limpiando workspace: {e}")
    
    def validate_terraform_code(self, terraform_code: str, project: Project) -> Dict[str, Any]:
        """
        Valida código Terraform usando terraform validate
        """
        workspace_dir = None
        try:
            # Crear workspace temporal
            workspace_dir = self.create_terraform_workspace(project, terraform_code)
            
            # Ejecutar terraform init
            init_result = self.terraform_init(workspace_dir, project)
            if not init_result['success']:
                return {
                    'valid': False,
                    'errors': [f"Error en terraform init: {init_result['stderr']}"]
                }
            
            # Ejecutar terraform validate
            validate_result = self.run_terraform_command(
                workspace_dir,
                ['validate'],
                project
            )
            
            return {
                'valid': validate_result['success'],
                'errors': [validate_result['stderr']] if not validate_result['success'] else [],
                'output': validate_result['stdout']
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [str(e)]
            }
        finally:
            if workspace_dir:
                self.cleanup_workspace(workspace_dir)

