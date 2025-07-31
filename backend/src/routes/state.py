from flask import Blueprint, request, jsonify
from src.models.project import db, Project
from src.services.state_service import StateService

state_bp = Blueprint('state', __name__)
state_service = StateService()

@state_bp.route('/state/test-connection', methods=['POST'])
def test_state_connection():
    """Prueba la conexión con el backend de estado configurado"""
    try:
        data = request.get_json()
        
        if not data.get('project_id'):
            return jsonify({'error': 'project_id is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.state_bucket_url:
            return jsonify({'error': 'No state bucket configured for this project'}), 400
        
        # Probar la conexión
        result = state_service.test_backend_connection(project)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Connection successful',
                'backend_type': result.get('backend_type', 'unknown')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@state_bp.route('/state/create-bucket', methods=['POST'])
def create_state_bucket():
    """Crea el bucket de estado para un proyecto"""
    try:
        data = request.get_json()
        
        if not data.get('project_id'):
            return jsonify({'error': 'project_id is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.state_bucket_url:
            return jsonify({'error': 'No state bucket URL configured for this project'}), 400
        
        # Crear el bucket
        result = state_service.create_state_bucket(project)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@state_bp.route('/state/backend-config/<int:project_id>', methods=['GET'])
def get_backend_config(project_id):
    """Obtiene la configuración del backend para un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if not project.state_bucket_url:
            return jsonify({
                'success': False,
                'error': 'No state bucket configured for this project'
            }), 400
        
        # Generar configuración del backend
        backend_content = state_service.generate_backend_tf_content(project)
        
        if backend_content:
            return jsonify({
                'success': True,
                'backend_content': backend_content,
                'bucket_url': project.state_bucket_url
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Could not generate backend configuration'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@state_bp.route('/state/configure-project', methods=['POST'])
def configure_project_state():
    """Configura el estado remoto para un proyecto"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['project_id', 'bucket_url', 'backend_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Validar tipo de backend
        backend_type = data['backend_type'].lower()
        bucket_url = data['bucket_url']
        
        if backend_type == 's3' and not bucket_url.startswith('s3://'):
            return jsonify({'error': 'S3 bucket URL must start with s3://'}), 400
        elif backend_type == 'gcs' and not bucket_url.startswith('gs://'):
            return jsonify({'error': 'GCS bucket URL must start with gs://'}), 400
        
        # Actualizar configuración del proyecto
        project.state_bucket_url = bucket_url
        
        # Configurar credenciales si se proporcionan
        if data.get('credentials'):
            project.set_state_bucket_credentials(data['credentials'])
        
        db.session.commit()
        
        # Probar la conexión
        test_result = state_service.test_backend_connection(project)
        
        return jsonify({
            'success': True,
            'message': 'Project state configuration updated',
            'connection_test': test_result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@state_bp.route('/state/supported-backends', methods=['GET'])
def get_supported_backends():
    """Obtiene la lista de backends de estado soportados"""
    try:
        backends = [
            {
                'type': 's3',
                'name': 'Amazon S3',
                'description': 'Almacenamiento de estado en Amazon S3',
                'url_format': 's3://bucket-name',
                'required_credentials': [
                    'access_key_id',
                    'secret_access_key',
                    'region'
                ],
                'optional_credentials': [
                    'dynamodb_table'
                ]
            },
            {
                'type': 'gcs',
                'name': 'Google Cloud Storage',
                'description': 'Almacenamiento de estado en Google Cloud Storage',
                'url_format': 'gs://bucket-name',
                'required_credentials': [
                    'service_account_json'
                ],
                'optional_credentials': []
            }
        ]
        
        return jsonify(backends), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@state_bp.route('/state/validate-config', methods=['POST'])
def validate_state_config():
    """Valida la configuración de estado antes de guardarla"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['bucket_url', 'backend_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        backend_type = data['backend_type'].lower()
        bucket_url = data['bucket_url']
        credentials = data.get('credentials', {})
        
        # Validaciones específicas por tipo de backend
        validation_errors = []
        
        if backend_type == 's3':
            if not bucket_url.startswith('s3://'):
                validation_errors.append('S3 bucket URL must start with s3://')
            
            required_creds = ['access_key_id', 'secret_access_key', 'region']
            for cred in required_creds:
                if not credentials.get(cred):
                    validation_errors.append(f'S3 credential "{cred}" is required')
        
        elif backend_type == 'gcs':
            if not bucket_url.startswith('gs://'):
                validation_errors.append('GCS bucket URL must start with gs://')
            
            if not credentials.get('service_account_json'):
                validation_errors.append('GCS service account JSON is required')
        
        else:
            validation_errors.append(f'Unsupported backend type: {backend_type}')
        
        if validation_errors:
            return jsonify({
                'valid': False,
                'errors': validation_errors
            }), 400
        
        return jsonify({
            'valid': True,
            'message': 'Configuration is valid'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

