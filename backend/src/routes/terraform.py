from flask import Blueprint, request, jsonify
from src.models.project import db, Project, TerraformPlan, Prompt
from src.services.terraform_service import TerraformService
from datetime import datetime

terraform_bp = Blueprint('terraform', __name__)
terraform_service = TerraformService()

@terraform_bp.route('/terraform/plan', methods=['POST'])
def create_terraform_plan():
    """Genera un plan de Terraform"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data.get('project_id') or not data.get('terraform_code'):
            return jsonify({'error': 'project_id and terraform_code are required'}), 400
        
        # Verificar que el proyecto existe
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        workspace_dir = None
        try:
            # Crear workspace temporal
            workspace_dir = terraform_service.create_terraform_workspace(
                project, data['terraform_code']
            )
            
            # Generar el plan
            plan_result = terraform_service.terraform_plan(
                workspace_dir, project, data.get('prompt_id')
            )
            
            if plan_result['success']:
                return jsonify({
                    'success': True,
                    'plan_id': plan_result['plan_id'],
                    'plan_output': plan_result['plan_output'],
                    'has_changes': plan_result['has_changes'],
                    'plan_json': plan_result.get('plan_json')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': plan_result['error']
                }), 500
                
        finally:
            if workspace_dir:
                terraform_service.cleanup_workspace(workspace_dir)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@terraform_bp.route('/terraform/plan/<int:plan_id>/approve', methods=['POST'])
def approve_terraform_plan(plan_id):
    """Aprueba un plan de Terraform"""
    try:
        terraform_plan = TerraformPlan.query.get_or_404(plan_id)
        
        if terraform_plan.status != 'pending':
            return jsonify({'error': 'Plan is not in pending status'}), 400
        
        terraform_plan.status = 'approved'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Plan approved successfully',
            'plan': terraform_plan.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@terraform_bp.route('/terraform/apply', methods=['POST'])
def apply_terraform_plan():
    """Aplica un plan de Terraform aprobado"""
    try:
        data = request.get_json()
        
        if not data.get('plan_id'):
            return jsonify({'error': 'plan_id is required'}), 400
        
        # Obtener el plan
        terraform_plan = TerraformPlan.query.get(data['plan_id'])
        if not terraform_plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        if terraform_plan.status != 'approved':
            return jsonify({'error': 'Plan is not approved'}), 400
        
        # Obtener el proyecto
        project = Project.query.get(terraform_plan.project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Obtener el código Terraform del prompt asociado
        prompt = None
        if terraform_plan.prompt_id:
            prompt = Prompt.query.get(terraform_plan.prompt_id)
        
        if not prompt or not prompt.terraform_code:
            return jsonify({'error': 'No Terraform code found for this plan'}), 400
        
        workspace_dir = None
        try:
            # Crear workspace temporal con el código
            workspace_dir = terraform_service.create_terraform_workspace(
                project, prompt.terraform_code
            )
            
            # Regenerar el plan (necesario para apply)
            plan_result = terraform_service.terraform_plan(workspace_dir, project)
            if not plan_result['success']:
                return jsonify({
                    'success': False,
                    'error': f"Error regenerating plan: {plan_result['error']}"
                }), 500
            
            # Aplicar el plan
            apply_result = terraform_service.terraform_apply(
                workspace_dir, project, terraform_plan.id
            )
            
            if apply_result['success']:
                # Actualizar el prompt asociado
                if prompt:
                    prompt.status = 'applied'
                    db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Terraform applied successfully',
                    'output': apply_result['output']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': apply_result['error']
                }), 500
                
        finally:
            if workspace_dir:
                terraform_service.cleanup_workspace(workspace_dir)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@terraform_bp.route('/terraform/validate', methods=['POST'])
def validate_terraform_code():
    """Valida código Terraform"""
    try:
        data = request.get_json()
        
        if not data.get('project_id') or not data.get('terraform_code'):
            return jsonify({'error': 'project_id and terraform_code are required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Validar el código
        validation_result = terraform_service.validate_terraform_code(
            data['terraform_code'], project
        )
        
        return jsonify(validation_result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@terraform_bp.route('/terraform/destroy', methods=['POST'])
def destroy_terraform_resources():
    """Destruye todos los recursos de Terraform de un proyecto"""
    try:
        data = request.get_json()
        
        if not data.get('project_id'):
            return jsonify({'error': 'project_id is required'}), 400
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Obtener el último código Terraform aplicado
        last_applied_prompt = Prompt.query.filter_by(
            project_id=project.id,
            status='applied'
        ).order_by(Prompt.created_at.desc()).first()
        
        if not last_applied_prompt or not last_applied_prompt.terraform_code:
            return jsonify({'error': 'No applied Terraform code found'}), 400
        
        workspace_dir = None
        try:
            # Crear workspace temporal
            workspace_dir = terraform_service.create_terraform_workspace(
                project, last_applied_prompt.terraform_code
            )
            
            # Ejecutar destroy
            destroy_result = terraform_service.terraform_destroy(workspace_dir, project)
            
            if destroy_result['success']:
                # Actualizar estado de prompts
                Prompt.query.filter_by(
                    project_id=project.id,
                    status='applied'
                ).update({'status': 'destroyed'})
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Resources destroyed successfully',
                    'output': destroy_result['output']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': destroy_result['error']
                }), 500
                
        finally:
            if workspace_dir:
                terraform_service.cleanup_workspace(workspace_dir)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@terraform_bp.route('/terraform/state/<int:project_id>', methods=['GET'])
def get_terraform_state(project_id):
    """Obtiene el estado actual de Terraform para un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Obtener el último código Terraform aplicado
        last_applied_prompt = Prompt.query.filter_by(
            project_id=project.id,
            status='applied'
        ).order_by(Prompt.created_at.desc()).first()
        
        if not last_applied_prompt or not last_applied_prompt.terraform_code:
            return jsonify({
                'success': False,
                'error': 'No applied Terraform code found'
            }), 404
        
        workspace_dir = None
        try:
            # Crear workspace temporal
            workspace_dir = terraform_service.create_terraform_workspace(
                project, last_applied_prompt.terraform_code
            )
            
            # Obtener el estado
            state_result = terraform_service.get_terraform_state(workspace_dir, project)
            
            return jsonify(state_result), 200
            
        finally:
            if workspace_dir:
                terraform_service.cleanup_workspace(workspace_dir)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@terraform_bp.route('/terraform/plans/<int:project_id>', methods=['GET'])
def get_project_terraform_plans(project_id):
    """Obtiene todos los planes de Terraform de un proyecto"""
    try:
        project = Project.query.get_or_404(project_id)
        plans = TerraformPlan.query.filter_by(project_id=project_id).order_by(
            TerraformPlan.created_at.desc()
        ).all()
        
        return jsonify([plan.to_dict() for plan in plans]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

