from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    cloud_provider = db.Column(db.String(50), nullable=False)  # AWS, Azure, GCP, etc.
    
    # Configuración del bucket para el estado de Terraform
    state_bucket_url = db.Column(db.String(255))
    state_bucket_credentials = db.Column(db.Text)  # JSON con credenciales
    
    # Configuración del repositorio Git
    git_repo_url = db.Column(db.String(255))
    git_ssh_key = db.Column(db.Text)
    
    # Configuración del LLM
    llm_provider = db.Column(db.String(50), default='gemini')  # gemini, openai, etc.
    llm_api_key = db.Column(db.String(255))
    system_prompt = db.Column(db.Text)  # Contexto personalizado
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    prompts = db.relationship('Prompt', backref='project', lazy=True, cascade='all, delete-orphan')
    terraform_plans = db.relationship('TerraformPlan', backref='project', lazy=True, cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cloud_provider': self.cloud_provider,
            'state_bucket_url': self.state_bucket_url,
            'git_repo_url': self.git_repo_url,
            'llm_provider': self.llm_provider,
            'system_prompt': self.system_prompt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_state_bucket_credentials(self):
        """Deserializa las credenciales del bucket de estado"""
        if self.state_bucket_credentials:
            return json.loads(self.state_bucket_credentials)
        return {}
    
    def set_state_bucket_credentials(self, credentials):
        """Serializa las credenciales del bucket de estado"""
        self.state_bucket_credentials = json.dumps(credentials)


class Prompt(db.Model):
    __tablename__ = 'prompts'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_prompt = db.Column(db.Text, nullable=False)
    llm_response = db.Column(db.Text)
    terraform_code = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, approved, applied, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_prompt': self.user_prompt,
            'llm_response': self.llm_response,
            'terraform_code': self.terraform_code,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TerraformPlan(db.Model):
    __tablename__ = 'terraform_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompts.id'), nullable=True)
    plan_output = db.Column(db.Text)
    plan_json = db.Column(db.Text)  # Plan en formato JSON
    status = db.Column(db.String(50), default='pending')  # pending, approved, applied, failed
    commit_message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applied_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'prompt_id': self.prompt_id,
            'plan_output': self.plan_output,
            'status': self.status,
            'commit_message': self.commit_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }


class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_name = db.Column(db.String(100), nullable=False)
    resource_address = db.Column(db.String(255), nullable=False)  # Dirección completa del recurso
    attributes = db.Column(db.Text)  # JSON con atributos del recurso
    dependencies = db.Column(db.Text)  # JSON con dependencias
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'resource_type': self.resource_type,
            'resource_name': self.resource_name,
            'resource_address': self.resource_address,
            'attributes': json.loads(self.attributes) if self.attributes else {},
            'dependencies': json.loads(self.dependencies) if self.dependencies else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_attributes(self, attributes):
        """Serializa los atributos del recurso"""
        self.attributes = json.dumps(attributes)
    
    def set_dependencies(self, dependencies):
        """Serializa las dependencias del recurso"""
        self.dependencies = json.dumps(dependencies)

