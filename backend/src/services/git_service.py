import os
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional
from src.models.project import Project

class GitService:
    """Servicio para la integración con repositorios Git (GitHub)"""
    
    def __init__(self):
        pass
    
    def clone_repository(self, project: Project, target_dir: str) -> Dict[str, Any]:
        """
        Clona el repositorio del proyecto
        
        Args:
            project: Proyecto con configuración de Git
            target_dir: Directorio donde clonar el repositorio
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            if not project.git_repo_url:
                return {
                    'success': False,
                    'error': 'No Git repository URL configured'
                }
            
            # Preparar credenciales SSH si están configuradas
            ssh_key_path = None
            if project.git_ssh_key:
                ssh_key_path = self._setup_ssh_key(project.git_ssh_key)
            
            # Configurar comando git clone
            env = os.environ.copy()
            if ssh_key_path:
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
            
            # Ejecutar git clone
            result = subprocess.run(
                ['git', 'clone', project.git_repo_url, target_dir],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            # Limpiar clave SSH temporal
            if ssh_key_path:
                self._cleanup_ssh_key(ssh_key_path)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Repository cloned successfully',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Git clone operation timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def commit_and_push(self, project: Project, repo_dir: str, commit_message: str, files_to_add: list = None) -> Dict[str, Any]:
        """
        Hace commit y push de los cambios al repositorio
        
        Args:
            project: Proyecto con configuración de Git
            repo_dir: Directorio del repositorio
            commit_message: Mensaje del commit
            files_to_add: Lista de archivos a agregar (None para agregar todos)
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            if not os.path.exists(repo_dir):
                return {
                    'success': False,
                    'error': 'Repository directory does not exist'
                }
            
            # Preparar credenciales SSH si están configuradas
            ssh_key_path = None
            if project.git_ssh_key:
                ssh_key_path = self._setup_ssh_key(project.git_ssh_key)
            
            # Configurar entorno
            env = os.environ.copy()
            if ssh_key_path:
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
            
            # Configurar usuario Git si no está configurado
            self._configure_git_user(repo_dir, env)
            
            # Agregar archivos
            if files_to_add:
                for file_path in files_to_add:
                    add_result = subprocess.run(
                        ['git', 'add', file_path],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                        env=env
                    )
                    if add_result.returncode != 0:
                        return {
                            'success': False,
                            'error': f'Error adding file {file_path}: {add_result.stderr}'
                        }
            else:
                # Agregar todos los archivos
                add_result = subprocess.run(
                    ['git', 'add', '.'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    env=env
                )
                if add_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Error adding files: {add_result.stderr}'
                    }
            
            # Verificar si hay cambios para hacer commit
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                env=env
            )
            
            if not status_result.stdout.strip():
                return {
                    'success': True,
                    'message': 'No changes to commit',
                    'commit_hash': None
                }
            
            # Hacer commit
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                env=env
            )
            
            if commit_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Error making commit: {commit_result.stderr}'
                }
            
            # Obtener hash del commit
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                env=env
            )
            
            commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else None
            
            # Hacer push
            push_result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            # Limpiar clave SSH temporal
            if ssh_key_path:
                self._cleanup_ssh_key(ssh_key_path)
            
            if push_result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Changes committed and pushed successfully',
                    'commit_hash': commit_hash,
                    'commit_message': commit_message
                }
            else:
                # Si el push falla, intentar con master en lugar de main
                push_master_result = subprocess.run(
                    ['git', 'push', 'origin', 'master'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60
                )
                
                if push_master_result.returncode == 0:
                    return {
                        'success': True,
                        'message': 'Changes committed and pushed successfully (master branch)',
                        'commit_hash': commit_hash,
                        'commit_message': commit_message
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error pushing to repository: {push_result.stderr}',
                        'commit_hash': commit_hash  # El commit se hizo pero el push falló
                    }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Git push operation timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_ssh_key(self, ssh_key_content: str) -> str:
        """
        Configura una clave SSH temporal para la autenticación
        
        Args:
            ssh_key_content: Contenido de la clave SSH privada
            
        Returns:
            str: Ruta del archivo de clave SSH temporal
        """
        # Crear archivo temporal para la clave SSH
        ssh_key_fd, ssh_key_path = tempfile.mkstemp(prefix='ssh_key_', suffix='.pem')
        
        try:
            with os.fdopen(ssh_key_fd, 'w') as f:
                f.write(ssh_key_content)
            
            # Configurar permisos correctos para la clave SSH
            os.chmod(ssh_key_path, 0o600)
            
            return ssh_key_path
        except Exception:
            # Si hay error, limpiar el archivo
            try:
                os.unlink(ssh_key_path)
            except:
                pass
            raise
    
    def _cleanup_ssh_key(self, ssh_key_path: str):
        """Limpia el archivo de clave SSH temporal"""
        try:
            if os.path.exists(ssh_key_path):
                os.unlink(ssh_key_path)
        except Exception:
            pass  # Ignorar errores de limpieza
    
    def _configure_git_user(self, repo_dir: str, env: dict):
        """Configura el usuario Git si no está configurado"""
        try:
            # Verificar si ya está configurado
            result = subprocess.run(
                ['git', 'config', 'user.email'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                # Configurar usuario por defecto
                subprocess.run(
                    ['git', 'config', 'user.email', 'genai-iac@platform.local'],
                    cwd=repo_dir,
                    env=env
                )
                subprocess.run(
                    ['git', 'config', 'user.name', 'GenAI-IaC Platform'],
                    cwd=repo_dir,
                    env=env
                )
        except Exception:
            pass  # Ignorar errores de configuración
    
    def test_git_connection(self, project: Project) -> Dict[str, Any]:
        """
        Prueba la conexión con el repositorio Git
        
        Args:
            project: Proyecto con configuración de Git
            
        Returns:
            Dict con el resultado de la prueba
        """
        try:
            if not project.git_repo_url:
                return {
                    'success': False,
                    'error': 'No Git repository URL configured'
                }
            
            # Crear directorio temporal para la prueba
            temp_dir = tempfile.mkdtemp(prefix='git_test_')
            
            try:
                # Intentar clonar el repositorio
                clone_result = self.clone_repository(project, temp_dir)
                
                if clone_result['success']:
                    return {
                        'success': True,
                        'message': 'Git connection successful',
                        'repository_url': project.git_repo_url
                    }
                else:
                    return {
                        'success': False,
                        'error': clone_result['error']
                    }
            finally:
                # Limpiar directorio temporal
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_repository_info(self, project: Project) -> Dict[str, Any]:
        """
        Obtiene información del repositorio
        
        Args:
            project: Proyecto con configuración de Git
            
        Returns:
            Dict con información del repositorio
        """
        try:
            if not project.git_repo_url:
                return {
                    'success': False,
                    'error': 'No Git repository URL configured'
                }
            
            # Crear directorio temporal
            temp_dir = tempfile.mkdtemp(prefix='git_info_')
            
            try:
                # Clonar el repositorio
                clone_result = self.clone_repository(project, temp_dir)
                
                if not clone_result['success']:
                    return {
                        'success': False,
                        'error': clone_result['error']
                    }
                
                # Obtener información del repositorio
                env = os.environ.copy()
                
                # Obtener último commit
                last_commit_result = subprocess.run(
                    ['git', 'log', '-1', '--format=%H|%an|%ae|%ad|%s'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                # Obtener rama actual
                branch_result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                # Obtener lista de archivos
                files_result = subprocess.run(
                    ['git', 'ls-files'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                repo_info = {
                    'repository_url': project.git_repo_url,
                    'current_branch': branch_result.stdout.strip() if branch_result.returncode == 0 else 'unknown',
                    'files': files_result.stdout.strip().split('\n') if files_result.returncode == 0 else []
                }
                
                # Parsear información del último commit
                if last_commit_result.returncode == 0:
                    commit_parts = last_commit_result.stdout.strip().split('|')
                    if len(commit_parts) >= 5:
                        repo_info['last_commit'] = {
                            'hash': commit_parts[0],
                            'author_name': commit_parts[1],
                            'author_email': commit_parts[2],
                            'date': commit_parts[3],
                            'message': commit_parts[4]
                        }
                
                return {
                    'success': True,
                    'repository_info': repo_info
                }
                
            finally:
                # Limpiar directorio temporal
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_terraform_code(self, project: Project, terraform_code: str, commit_message: str) -> Dict[str, Any]:
        """
        Sincroniza el código Terraform con el repositorio Git
        
        Args:
            project: Proyecto con configuración de Git
            terraform_code: Código Terraform a sincronizar
            commit_message: Mensaje del commit
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            if not project.git_repo_url:
                return {
                    'success': False,
                    'error': 'No Git repository URL configured'
                }
            
            # Crear directorio temporal
            temp_dir = tempfile.mkdtemp(prefix='git_sync_')
            
            try:
                # Clonar el repositorio
                clone_result = self.clone_repository(project, temp_dir)
                
                if not clone_result['success']:
                    return {
                        'success': False,
                        'error': clone_result['error']
                    }
                
                # Escribir el código Terraform
                main_tf_path = os.path.join(temp_dir, 'main.tf')
                with open(main_tf_path, 'w') as f:
                    f.write(terraform_code)
                
                # Hacer commit y push
                push_result = self.commit_and_push(
                    project, temp_dir, commit_message, ['main.tf']
                )
                
                return push_result
                
            finally:
                # Limpiar directorio temporal
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

