from flask import Blueprint, request, jsonify
from src.models.project import db, Project
from src.services.git_service import GitService

git_bp = Blueprint('git', __name__)
git_service = GitService()

@git_bp.route('/git/test-connection', methods=['POST'])
def test_git_connection():
    """Prueba la conexión con el repositorio Git configurado"""
    try:
        data = request.get_json()
        
        if not data.get('project_id'):
            return jsonify({'error': 'project_id is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.git_repo_url:
            return jsonify({'error': 'No Git repository configured for this project'}), 400
        
        # Probar la conexión
        result = git_service.test_git_connection(project)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'repository_url': result.get('repository_url')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@git_bp.route('/git/repository-info/<int:project_id>', methods=['GET'])
def get_repository_info(project_id):
    """Obtiene información del repositorio Git de un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if not project.git_repo_url:
            return jsonify({'error': 'No Git repository configured for this project'}), 400
        
        # Obtener información del repositorio
        result = git_service.get_repository_info(project)
        
        if result['success']:
            return jsonify({
                'success': True,
                'repository_info': result['repository_info']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@git_bp.route('/git/sync-terraform', methods=['POST'])
def sync_terraform_code():
    """Sincroniza código Terraform con el repositorio Git"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['project_id', 'terraform_code', 'commit_message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.git_repo_url:
            return jsonify({'error': 'No Git repository configured for this project'}), 400
        
        # Sincronizar código
        result = git_service.sync_terraform_code(
            project=project,
            terraform_code=data['terraform_code'],
            commit_message=data['commit_message']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'commit_hash': result.get('commit_hash'),
                'commit_message': result.get('commit_message')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'commit_hash': result.get('commit_hash')  # Puede haber commit pero fallar el push
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@git_bp.route('/git/configure-project', methods=['POST'])
def configure_project_git():
    """Configura la integración Git para un proyecto"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data.get('project_id') or not data.get('git_repo_url'):
            return jsonify({'error': 'project_id and git_repo_url are required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Actualizar configuración del proyecto
        project.git_repo_url = data['git_repo_url']
        
        # Configurar clave SSH si se proporciona
        if data.get('git_ssh_key'):
            project.git_ssh_key = data['git_ssh_key']
        
        db.session.commit()
        
        # Probar la conexión
        test_result = git_service.test_git_connection(project)
        
        return jsonify({
            'success': True,
            'message': 'Git configuration updated',
            'connection_test': test_result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@git_bp.route('/git/validate-config', methods=['POST'])
def validate_git_config():
    """Valida la configuración Git antes de guardarla"""
    try:
        data = request.get_json()
        
        if not data.get('git_repo_url'):
            return jsonify({'error': 'git_repo_url is required'}), 400
        
        git_repo_url = data['git_repo_url']
        git_ssh_key = data.get('git_ssh_key')
        
        # Validaciones básicas
        validation_errors = []
        
        # Validar formato de URL
        if not (git_repo_url.startswith('https://') or git_repo_url.startswith('git@')):
            validation_errors.append('Git repository URL must start with https:// or git@')
        
        # Validar que sea un repositorio Git válido
        if not (git_repo_url.endswith('.git') or 'github.com' in git_repo_url or 'gitlab.com' in git_repo_url):
            validation_errors.append('Git repository URL does not appear to be valid')
        
        # Validar clave SSH si se proporciona
        if git_ssh_key:
            if not git_ssh_key.startswith('-----BEGIN'):
                validation_errors.append('SSH key does not appear to be in valid format')
        
        if validation_errors:
            return jsonify({
                'valid': False,
                'errors': validation_errors
            }), 400
        
        return jsonify({
            'valid': True,
            'message': 'Git configuration is valid'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@git_bp.route('/git/supported-providers', methods=['GET'])
def get_supported_git_providers():
    """Obtiene la lista de proveedores Git soportados"""
    try:
        providers = [
            {
                'name': 'GitHub',
                'description': 'Repositorios en GitHub.com',
                'url_format': 'https://github.com/username/repository.git',
                'ssh_format': 'git@github.com:username/repository.git',
                'supports_ssh': True,
                'supports_https': True
            },
            {
                'name': 'GitLab',
                'description': 'Repositorios en GitLab.com',
                'url_format': 'https://gitlab.com/username/repository.git',
                'ssh_format': 'git@gitlab.com:username/repository.git',
                'supports_ssh': True,
                'supports_https': True
            },
            {
                'name': 'Bitbucket',
                'description': 'Repositorios en Bitbucket.org',
                'url_format': 'https://bitbucket.org/username/repository.git',
                'ssh_format': 'git@bitbucket.org:username/repository.git',
                'supports_ssh': True,
                'supports_https': True
            },
            {
                'name': 'Custom Git',
                'description': 'Servidor Git personalizado',
                'url_format': 'https://your-git-server.com/repository.git',
                'ssh_format': 'git@your-git-server.com:repository.git',
                'supports_ssh': True,
                'supports_https': True
            }
        ]
        
        return jsonify(providers), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@git_bp.route('/git/commit-history/<int:project_id>', methods=['GET'])
def get_commit_history(project_id):
    """Obtiene el historial de commits de un proyecto (simulado por ahora)"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if not project.git_repo_url:
            return jsonify({'error': 'No Git repository configured for this project'}), 400
        
        # Por ahora, devolver historial simulado
        # En una implementación completa, se obtendría del repositorio real
        commits = [
            {
                'hash': 'abc123def456',
                'message': 'Initial Terraform configuration',
                'author': 'GenAI-IaC Platform',
                'date': '2024-01-15T10:30:00Z',
                'files_changed': ['main.tf']
            }
        ]
        
        return jsonify({
            'success': True,
            'commits': commits,
            'repository_url': project.git_repo_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

