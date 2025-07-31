from flask import Blueprint, request, jsonify
from src.models.project import db, Project, Prompt, TerraformPlan, Resource
from datetime import datetime

project_bp = Blueprint('project', __name__)

@project_bp.route('/projects', methods=['GET'])
def get_projects():
    """Obtiene todos los proyectos"""
    try:
        projects = Project.query.all()
        return jsonify([project.to_dict() for project in projects]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects', methods=['POST'])
def create_project():
    """Crea un nuevo proyecto"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data.get('name') or not data.get('cloud_provider'):
            return jsonify({'error': 'Name and cloud_provider are required'}), 400
        
        # Verificar que el nombre no exista
        existing_project = Project.query.filter_by(name=data['name']).first()
        if existing_project:
            return jsonify({'error': 'Project name already exists'}), 400
        
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            cloud_provider=data['cloud_provider'],
            state_bucket_url=data.get('state_bucket_url'),
            git_repo_url=data.get('git_repo_url'),
            git_ssh_key=data.get('git_ssh_key'),
            llm_provider=data.get('llm_provider', 'gemini'),
            llm_api_key=data.get('llm_api_key'),
            system_prompt=data.get('system_prompt', '')
        )
        
        # Configurar credenciales del bucket si se proporcionan
        if data.get('state_bucket_credentials'):
            project.set_state_bucket_credentials(data['state_bucket_credentials'])
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify(project.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Obtiene un proyecto específico"""
    try:
        project = Project.query.get_or_404(project_id)
        return jsonify(project.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Actualiza un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        # Actualizar campos
        if 'name' in data:
            # Verificar que el nuevo nombre no exista
            existing_project = Project.query.filter_by(name=data['name']).filter(Project.id != project_id).first()
            if existing_project:
                return jsonify({'error': 'Project name already exists'}), 400
            project.name = data['name']
        
        if 'description' in data:
            project.description = data['description']
        if 'cloud_provider' in data:
            project.cloud_provider = data['cloud_provider']
        if 'state_bucket_url' in data:
            project.state_bucket_url = data['state_bucket_url']
        if 'git_repo_url' in data:
            project.git_repo_url = data['git_repo_url']
        if 'git_ssh_key' in data:
            project.git_ssh_key = data['git_ssh_key']
        if 'llm_provider' in data:
            project.llm_provider = data['llm_provider']
        if 'llm_api_key' in data:
            project.llm_api_key = data['llm_api_key']
        if 'system_prompt' in data:
            project.system_prompt = data['system_prompt']
        
        # Actualizar credenciales del bucket si se proporcionan
        if 'state_bucket_credentials' in data:
            project.set_state_bucket_credentials(data['state_bucket_credentials'])
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(project.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Elimina un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': 'Project deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>/prompts', methods=['GET'])
def get_project_prompts(project_id):
    """Obtiene el historial de prompts de un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        prompts = Prompt.query.filter_by(project_id=project_id).order_by(Prompt.created_at.desc()).all()
        return jsonify([prompt.to_dict() for prompt in prompts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>/resources', methods=['GET'])
def get_project_resources(project_id):
    """Obtiene el inventario de recursos de un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        resources = Resource.query.filter_by(project_id=project_id).all()
        return jsonify([resource.to_dict() for resource in resources]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>/plans', methods=['GET'])
def get_project_plans(project_id):
    """Obtiene el historial de planes de Terraform de un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        plans = TerraformPlan.query.filter_by(project_id=project_id).order_by(TerraformPlan.created_at.desc()).all()
        return jsonify([plan.to_dict() for plan in plans]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

