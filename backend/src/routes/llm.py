from flask import Blueprint, request, jsonify
import asyncio
from src.models.project import db, Project, Prompt
from src.services.llm_service import LLMService
from datetime import datetime

llm_bp = Blueprint('llm', __name__)
llm_service = LLMService()

@llm_bp.route('/llm/process-prompt', methods=['POST'])
def process_prompt():
    """Procesa un prompt del usuario usando LLM"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data.get('project_id') or not data.get('user_prompt'):
            return jsonify({'error': 'project_id and user_prompt are required'}), 400
        
        # Verificar que el proyecto existe
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Verificar que el proyecto tiene configuración de LLM
        if not project.llm_api_key:
            return jsonify({'error': 'Project does not have LLM API key configured'}), 400
        
        # Crear el prompt en la base de datos
        prompt = Prompt(
            project_id=data['project_id'],
            user_prompt=data['user_prompt'],
            status='processing'
        )
        db.session.add(prompt)
        db.session.commit()
        
        try:
            # Procesar el prompt con el LLM (ejecutar de forma síncrona)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                llm_service.process_prompt(
                    project=project,
                    user_prompt=data['user_prompt'],
                    existing_terraform=data.get('existing_terraform')
                )
            )
            
            if result['success']:
                # Actualizar el prompt con la respuesta
                prompt.llm_response = result['llm_response']
                prompt.terraform_code = result['terraform_code']
                prompt.status = 'completed'
                
                # Validar sintaxis básica del código Terraform
                if result['terraform_code']:
                    validation = llm_service.validate_terraform_syntax(result['terraform_code'])
                    if not validation['valid']:
                        prompt.status = 'validation_failed'
                        result['validation_issues'] = validation['issues']
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'prompt_id': prompt.id,
                    'analysis': result.get('analysis', ''),
                    'terraform_code': result.get('terraform_code', ''),
                    'commit_message': result.get('commit_message', ''),
                    'model_used': result.get('model_used', ''),
                    'validation_issues': result.get('validation_issues', [])
                }), 200
            else:
                # Error en el procesamiento
                prompt.status = 'failed'
                prompt.llm_response = f"Error: {result['error']}"
                db.session.commit()
                
                return jsonify({
                    'success': False,
                    'error': result['error'],
                    'prompt_id': prompt.id
                }), 500
                
        except Exception as e:
            # Error en el procesamiento
            prompt.status = 'failed'
            prompt.llm_response = f"Error: {str(e)}"
            db.session.commit()
            
            return jsonify({
                'success': False,
                'error': str(e),
                'prompt_id': prompt.id
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/llm/validate-terraform', methods=['POST'])
def validate_terraform():
    """Valida la sintaxis de código Terraform"""
    try:
        data = request.get_json()
        
        if not data.get('terraform_code'):
            return jsonify({'error': 'terraform_code is required'}), 400
        
        validation = llm_service.validate_terraform_syntax(data['terraform_code'])
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/llm/models', methods=['GET'])
def get_available_models():
    """Obtiene la lista de modelos LLM disponibles"""
    try:
        models = [
            {
                'provider': 'gemini',
                'name': 'Gemini 1.5 Flash',
                'model_id': 'gemini/gemini-1.5-flash',
                'description': 'Modelo rápido y eficiente de Google'
            },
            {
                'provider': 'openai',
                'name': 'GPT-4o Mini',
                'model_id': 'gpt-4o-mini',
                'description': 'Modelo compacto y eficiente de OpenAI'
            },
            {
                'provider': 'claude',
                'name': 'Claude 3 Haiku',
                'model_id': 'claude-3-haiku-20240307',
                'description': 'Modelo rápido de Anthropic'
            }
        ]
        
        return jsonify(models), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/llm/test-connection', methods=['POST'])
def test_llm_connection():
    """Prueba la conexión con el LLM configurado en un proyecto"""
    try:
        data = request.get_json()
        
        if not data.get('project_id'):
            return jsonify({'error': 'project_id is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.llm_api_key:
            return jsonify({'error': 'Project does not have LLM API key configured'}), 400
        
        # Realizar una prueba simple con el LLM
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            llm_service.process_prompt(
                project=project,
                user_prompt="Test de conexión - responde solo 'OK'",
                existing_terraform=None
            )
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Conexión exitosa',
                'model_used': result.get('model_used', '')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

