from flask import Blueprint, request, jsonify
from src.models.project import db, Project, Prompt
from datetime import datetime

prompt_bp = Blueprint('prompt', __name__)

@prompt_bp.route('/prompts', methods=['POST'])
def create_prompt():
    """Crea un nuevo prompt y lo procesa"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data.get('project_id') or not data.get('user_prompt'):
            return jsonify({'error': 'project_id and user_prompt are required'}), 400
        
        # Verificar que el proyecto existe
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Crear el prompt
        prompt = Prompt(
            project_id=data['project_id'],
            user_prompt=data['user_prompt'],
            status='pending'
        )
        
        db.session.add(prompt)
        db.session.commit()
        
        # TODO: Aquí se integrará el procesamiento con LLM
        # Por ahora, solo devolvemos el prompt creado
        
        return jsonify(prompt.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prompt_bp.route('/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """Obtiene un prompt específico"""
    try:
        prompt = Prompt.query.get_or_404(prompt_id)
        return jsonify(prompt.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prompt_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """Actualiza un prompt (principalmente para cambiar el estado)"""
    try:
        prompt = Prompt.query.get_or_404(prompt_id)
        data = request.get_json()
        
        if 'llm_response' in data:
            prompt.llm_response = data['llm_response']
        if 'terraform_code' in data:
            prompt.terraform_code = data['terraform_code']
        if 'status' in data:
            prompt.status = data['status']
        
        db.session.commit()
        
        return jsonify(prompt.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prompt_bp.route('/prompts', methods=['GET'])
def get_prompts():
    """Obtiene todos los prompts (con filtros opcionales)"""
    try:
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        
        query = Prompt.query
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        if status:
            query = query.filter_by(status=status)
        
        prompts = query.order_by(Prompt.created_at.desc()).all()
        return jsonify([prompt.to_dict() for prompt in prompts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

