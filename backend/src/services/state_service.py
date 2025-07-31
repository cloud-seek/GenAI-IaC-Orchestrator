import os
import json
import boto3
from google.cloud import storage as gcs
from typing import Dict, Any, Optional
from src.models.project import Project

class StateService:
    """Servicio para la gestión del estado centralizada de Terraform"""
    
    def __init__(self):
        pass
    
    def configure_s3_backend(self, project: Project) -> Dict[str, Any]:
        """
        Configura el backend S3 para el estado de Terraform
        
        Args:
            project: Proyecto con configuración de S3
            
        Returns:
            Dict con la configuración del backend
        """
        try:
            if not project.state_bucket_url or not project.state_bucket_url.startswith('s3://'):
                return {
                    'success': False,
                    'error': 'Invalid S3 bucket URL'
                }
            
            # Extraer información del bucket
            bucket_url = project.state_bucket_url.replace('s3://', '')
            bucket_parts = bucket_url.split('/')
            bucket_name = bucket_parts[0]
            
            # Obtener credenciales del proyecto
            credentials = project.get_state_bucket_credentials()
            
            # Configurar cliente S3
            s3_client = self._get_s3_client(credentials)
            
            # Verificar que el bucket existe y es accesible
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Cannot access S3 bucket: {str(e)}'
                }
            
            # Generar configuración del backend
            backend_config = {
                'bucket': bucket_name,
                'key': f"{project.name}/terraform.tfstate",
                'region': credentials.get('region', 'us-east-1'),
                'encrypt': True
            }
            
            # Agregar configuración de DynamoDB para locking si está disponible
            if credentials.get('dynamodb_table'):
                backend_config['dynamodb_table'] = credentials['dynamodb_table']
            
            return {
                'success': True,
                'backend_config': backend_config,
                'backend_type': 's3'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def configure_gcs_backend(self, project: Project) -> Dict[str, Any]:
        """
        Configura el backend GCS para el estado de Terraform
        
        Args:
            project: Proyecto con configuración de GCS
            
        Returns:
            Dict con la configuración del backend
        """
        try:
            if not project.state_bucket_url or not project.state_bucket_url.startswith('gs://'):
                return {
                    'success': False,
                    'error': 'Invalid GCS bucket URL'
                }
            
            # Extraer información del bucket
            bucket_url = project.state_bucket_url.replace('gs://', '')
            bucket_parts = bucket_url.split('/')
            bucket_name = bucket_parts[0]
            
            # Obtener credenciales del proyecto
            credentials = project.get_state_bucket_credentials()
            
            # Configurar cliente GCS
            gcs_client = self._get_gcs_client(credentials)
            
            # Verificar que el bucket existe y es accesible
            try:
                bucket = gcs_client.bucket(bucket_name)
                bucket.reload()
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Cannot access GCS bucket: {str(e)}'
                }
            
            # Generar configuración del backend
            backend_config = {
                'bucket': bucket_name,
                'prefix': f"{project.name}"
            }
            
            return {
                'success': True,
                'backend_config': backend_config,
                'backend_type': 'gcs'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_s3_client(self, credentials: Dict[str, Any]):
        """Crea un cliente S3 con las credenciales proporcionadas"""
        session = boto3.Session(
            aws_access_key_id=credentials.get('access_key_id'),
            aws_secret_access_key=credentials.get('secret_access_key'),
            region_name=credentials.get('region', 'us-east-1')
        )
        return session.client('s3')
    
    def _get_gcs_client(self, credentials: Dict[str, Any]):
        """Crea un cliente GCS con las credenciales proporcionadas"""
        # Para GCS, las credenciales suelen ser un archivo JSON de service account
        if credentials.get('service_account_json'):
            # Escribir las credenciales a un archivo temporal
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(credentials['service_account_json'], f)
                credentials_path = f.name
            
            # Configurar variable de entorno
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            return gcs.Client()
        else:
            # Usar credenciales por defecto del entorno
            return gcs.Client()
    
    def test_backend_connection(self, project: Project) -> Dict[str, Any]:
        """
        Prueba la conexión con el backend configurado
        
        Args:
            project: Proyecto a probar
            
        Returns:
            Dict con el resultado de la prueba
        """
        try:
            if not project.state_bucket_url:
                return {
                    'success': False,
                    'error': 'No state bucket configured'
                }
            
            if project.state_bucket_url.startswith('s3://'):
                return self.configure_s3_backend(project)
            elif project.state_bucket_url.startswith('gs://'):
                return self.configure_gcs_backend(project)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported backend type'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_backend_tf_content(self, project: Project) -> str:
        """
        Genera el contenido del archivo backend.tf para un proyecto
        
        Args:
            project: Proyecto para el cual generar la configuración
            
        Returns:
            str: Contenido del archivo backend.tf
        """
        if not project.state_bucket_url:
            return ""
        
        if project.state_bucket_url.startswith('s3://'):
            config_result = self.configure_s3_backend(project)
            if config_result['success']:
                config = config_result['backend_config']
                content = f'''terraform {{
  backend "s3" {{
    bucket = "{config['bucket']}"
    key    = "{config['key']}"
    region = "{config['region']}"
    encrypt = {str(config['encrypt']).lower()}'''
                
                if config.get('dynamodb_table'):
                    content += f'\n    dynamodb_table = "{config["dynamodb_table"]}"'
                
                content += '''
  }
}'''
                return content
        
        elif project.state_bucket_url.startswith('gs://'):
            config_result = self.configure_gcs_backend(project)
            if config_result['success']:
                config = config_result['backend_config']
                return f'''terraform {{
  backend "gcs" {{
    bucket = "{config['bucket']}"
    prefix = "{config['prefix']}"
  }}
}}'''
        
        return ""
    
    def create_state_bucket(self, project: Project) -> Dict[str, Any]:
        """
        Crea el bucket de estado si no existe
        
        Args:
            project: Proyecto para el cual crear el bucket
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            if not project.state_bucket_url:
                return {
                    'success': False,
                    'error': 'No state bucket URL configured'
                }
            
            credentials = project.get_state_bucket_credentials()
            
            if project.state_bucket_url.startswith('s3://'):
                return self._create_s3_bucket(project, credentials)
            elif project.state_bucket_url.startswith('gs://'):
                return self._create_gcs_bucket(project, credentials)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported backend type'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_s3_bucket(self, project: Project, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un bucket S3 si no existe"""
        try:
            bucket_name = project.state_bucket_url.replace('s3://', '').split('/')[0]
            s3_client = self._get_s3_client(credentials)
            
            # Verificar si el bucket ya existe
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                return {
                    'success': True,
                    'message': 'Bucket already exists'
                }
            except:
                pass
            
            # Crear el bucket
            region = credentials.get('region', 'us-east-1')
            if region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            # Habilitar versionado
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Habilitar encriptación
            s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }]
                }
            )
            
            return {
                'success': True,
                'message': 'S3 bucket created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error creating S3 bucket: {str(e)}'
            }
    
    def _create_gcs_bucket(self, project: Project, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un bucket GCS si no existe"""
        try:
            bucket_name = project.state_bucket_url.replace('gs://', '').split('/')[0]
            gcs_client = self._get_gcs_client(credentials)
            
            # Verificar si el bucket ya existe
            try:
                bucket = gcs_client.bucket(bucket_name)
                bucket.reload()
                return {
                    'success': True,
                    'message': 'Bucket already exists'
                }
            except:
                pass
            
            # Crear el bucket
            bucket = gcs_client.bucket(bucket_name)
            bucket = gcs_client.create_bucket(bucket)
            
            # Habilitar versionado
            bucket.versioning_enabled = True
            bucket.patch()
            
            return {
                'success': True,
                'message': 'GCS bucket created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error creating GCS bucket: {str(e)}'
            }

