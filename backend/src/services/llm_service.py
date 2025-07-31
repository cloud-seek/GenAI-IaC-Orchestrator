import os
import json
from typing import Dict, Any, Optional
from litellm import completion
from src.models.project import Project

class LLMService:
    """Servicio para la integración con LLMs usando LiteLLM"""
    
    def __init__(self):
        self.default_system_prompt = """
Eres un experto en Infraestructura como Código (IaC) especializado en Terraform.
Tu tarea es analizar las solicitudes de los usuarios y generar código Terraform apropiado.

Instrucciones:
1. Analiza cuidadosamente la solicitud del usuario
2. Genera código Terraform válido y bien estructurado
3. Incluye comentarios explicativos en el código
4. Considera las mejores prácticas de seguridad y eficiencia
5. Si la solicitud no es clara, solicita aclaraciones específicas
6. Proporciona un mensaje de commit descriptivo para el control de versiones

Formato de respuesta:
- Análisis: Breve explicación de lo que se va a crear/modificar
- Código Terraform: El código generado
- Mensaje de commit: Un mensaje descriptivo para el commit
"""
    
    def get_project_system_prompt(self, project: Project) -> str:
        """Obtiene el system prompt personalizado del proyecto o el por defecto"""
        if project.system_prompt and project.system_prompt.strip():
            return project.system_prompt
        return self.default_system_prompt
    
    def get_llm_config(self, project: Project) -> Dict[str, Any]:
        """Obtiene la configuración del LLM para el proyecto"""
        config = {
            "model": self._get_model_name(project.llm_provider),
            "temperature": 0.1,  # Baja temperatura para respuestas más deterministas
            "max_tokens": 2000,
        }
        
        # Configurar API key si está disponible
        if project.llm_api_key:
            if project.llm_provider == 'gemini':
                os.environ['GEMINI_API_KEY'] = project.llm_api_key
            elif project.llm_provider == 'openai':
                os.environ['OPENAI_API_KEY'] = project.llm_api_key
        
        return config
    
    def _get_model_name(self, provider: str) -> str:
        """Mapea el proveedor al nombre del modelo en LiteLLM"""
        model_mapping = {
            'gemini': 'gemini/gemini-1.5-flash',
            'openai': 'gpt-4o-mini',
            'claude': 'claude-3-haiku-20240307'
        }
        return model_mapping.get(provider, 'gemini/gemini-1.5-flash')
    
    async def process_prompt(self, project: Project, user_prompt: str, existing_terraform: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa un prompt del usuario y genera código Terraform
        
        Args:
            project: Proyecto asociado
            user_prompt: Prompt del usuario
            existing_terraform: Código Terraform existente (opcional)
            
        Returns:
            Dict con la respuesta del LLM, código Terraform y mensaje de commit
        """
        try:
            system_prompt = self.get_project_system_prompt(project)
            llm_config = self.get_llm_config(project)
            
            # Construir el contexto del mensaje
            context_parts = [
                f"Proyecto: {project.name}",
                f"Proveedor de nube: {project.cloud_provider}",
                f"Solicitud del usuario: {user_prompt}"
            ]
            
            if existing_terraform:
                context_parts.append(f"Código Terraform existente:\n```hcl\n{existing_terraform}\n```")
            
            context = "\n\n".join(context_parts)
            
            # Realizar la llamada al LLM
            response = completion(
                model=llm_config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=llm_config["temperature"],
                max_tokens=llm_config["max_tokens"]
            )
            
            llm_response = response.choices[0].message.content
            
            # Parsear la respuesta para extraer componentes
            parsed_response = self._parse_llm_response(llm_response)
            
            return {
                "success": True,
                "llm_response": llm_response,
                "analysis": parsed_response.get("analysis", ""),
                "terraform_code": parsed_response.get("terraform_code", ""),
                "commit_message": parsed_response.get("commit_message", "Actualización de infraestructura"),
                "model_used": llm_config["model"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "llm_response": None,
                "terraform_code": None,
                "commit_message": None
            }
    
    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """
        Parsea la respuesta del LLM para extraer componentes estructurados
        """
        result = {
            "analysis": "",
            "terraform_code": "",
            "commit_message": ""
        }
        
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detectar secciones
            if 'análisis' in line_lower or 'analysis' in line_lower:
                if current_section and current_content:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'analysis'
                current_content = []
            elif 'terraform' in line_lower and ('código' in line_lower or 'code' in line_lower):
                if current_section and current_content:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'terraform_code'
                current_content = []
            elif 'commit' in line_lower and ('mensaje' in line_lower or 'message' in line_lower):
                if current_section and current_content:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'commit_message'
                current_content = []
            elif line.strip().startswith('```'):
                # Manejar bloques de código
                if current_section == 'terraform_code':
                    continue
            else:
                if current_section:
                    current_content.append(line)
        
        # Agregar el último contenido
        if current_section and current_content:
            result[current_section] = '\n'.join(current_content).strip()
        
        # Si no se encontraron secciones estructuradas, usar toda la respuesta como análisis
        if not any(result.values()):
            result['analysis'] = response.strip()
        
        # Limpiar código Terraform de marcadores de código
        if result['terraform_code']:
            terraform_code = result['terraform_code']
            # Remover marcadores de código markdown
            terraform_code = terraform_code.replace('```hcl', '').replace('```terraform', '').replace('```', '')
            result['terraform_code'] = terraform_code.strip()
        
        return result
    
    def validate_terraform_syntax(self, terraform_code: str) -> Dict[str, Any]:
        """
        Valida la sintaxis básica del código Terraform
        Nota: Esta es una validación básica, la validación completa se hará con terraform validate
        """
        try:
            # Validaciones básicas
            issues = []
            
            if not terraform_code.strip():
                issues.append("El código Terraform está vacío")
                return {"valid": False, "issues": issues}
            
            # Verificar que tenga estructura básica de Terraform
            if 'resource' not in terraform_code and 'data' not in terraform_code and 'module' not in terraform_code:
                issues.append("El código no contiene recursos, datos o módulos de Terraform")
            
            # Verificar balanceado de llaves
            open_braces = terraform_code.count('{')
            close_braces = terraform_code.count('}')
            if open_braces != close_braces:
                issues.append(f"Llaves desbalanceadas: {open_braces} abiertas, {close_braces} cerradas")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Error en validación: {str(e)}"]
            }

