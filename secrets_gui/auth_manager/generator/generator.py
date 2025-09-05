#!/usr/bin/env python3
"""
Authenticator Generator Service
Generates new authenticator modules from templates or using Claude Code.
"""

import os
import re
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Template, Environment, FileSystemLoader
import logging

from .validator import AuthenticatorValidator

class AuthenticatorGenerator:
    """Generator for creating new authenticator modules."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.templates_dir = self.base_dir / "templates"
        self.output_dir = self.base_dir / "authenticators"
        self.logger = logging.getLogger("auth.generator")
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load template metadata
        self.metadata = self._load_metadata()
        
        # Initialize validator
        self.validator = AuthenticatorValidator()
        
        # Check Claude availability
        self.claude_available = self._check_claude_availability()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load template metadata from YAML file."""
        metadata_path = self.templates_dir / "metadata.yaml"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return yaml.safe_load(f)
        return {"templates": {}}
    
    def _check_claude_availability(self) -> bool:
        """Check if Claude Code CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List available templates with their metadata."""
        templates = []
        for template_id, template_data in self.metadata.get("templates", {}).items():
            templates.append({
                "id": template_id,
                "name": template_data.get("name", template_id),
                "description": template_data.get("description", ""),
                "icon": template_data.get("icon", "📄"),
                "required_fields": template_data.get("required_fields", []),
                "optional_fields": template_data.get("optional_fields", []),
                "examples": template_data.get("examples", [])
            })
        return templates
    
    def get_template_fields(self, template_id: str) -> Dict[str, Any]:
        """Get required and optional fields for a template."""
        if template_id not in self.metadata.get("templates", {}):
            return {"error": f"Unknown template: {template_id}"}
            
        template_data = self.metadata.get("templates", {}).get(template_id, {})
        return {
            "name": template_data.get("name", template_id),
            "description": template_data.get("description", ""),
            "required_fields": template_data.get("required_fields", []),
            "optional_fields": template_data.get("optional_fields", []),
            "field_descriptions": template_data.get("field_descriptions", {}),
            "example": template_data.get("example", {})
        }
    
    def generate_authenticator(
        self,
        service_name: str,
        template_type: str,
        parameters: Dict[str, Any],
        use_claude: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a new authenticator module.
        
        Args:
            service_name: Display name of the service (e.g., "Vercel")
            template_type: Template ID to use (e.g., "cli_token")
            parameters: Template parameters
            use_claude: Whether to use Claude for generation
        
        Returns:
            dict: Generation result with success status and details
        """
        # Sanitize service name for use in code
        service_id = self._sanitize_service_id(service_name)
        service_class_name = self._to_class_name(service_name)
        
        # Add computed values to parameters
        parameters["service_id"] = service_id
        parameters["service_display_name"] = service_name
        parameters["service_class_name"] = service_class_name
        
        if use_claude and self.claude_available:
            return self._generate_with_claude(service_name, parameters)
        else:
            return self._generate_from_template(
                service_name,
                template_type,
                parameters
            )
    
    def _generate_from_template(
        self,
        service_name: str,
        template_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate authenticator from a template."""
        # Check if template exists
        template_file = f"{template_type}.py.j2"
        if template_file not in self.jinja_env.list_templates():
            return {
                "success": False,
                "message": f"Template '{template_type}' not found"
            }
        
        # Validate parameters
        validation = self._validate_parameters(template_type, parameters)
        if not validation["valid"]:
            return {
                "success": False,
                "message": validation["error"],
                "missing_fields": validation.get("missing_fields", [])
            }
        
        try:
            # Load and render template
            template = self.jinja_env.get_template(template_file)
            code = template.render(**parameters)
            
            # Validate generated code
            syntax_check = self.validator.validate_syntax(code)
            if not syntax_check["valid"]:
                return {
                    "success": False,
                    "message": f"Generated code has syntax errors: {syntax_check['error']}"
                }
            
            # Check authenticator structure
            structure_check = self.validator.validate_structure(code)
            if not structure_check["valid"]:
                return {
                    "success": False,
                    "message": f"Generated code missing required methods: {structure_check['missing_methods']}"
                }
            
            # Save to file
            filename = f"{parameters['service_id']}_auth.py"
            file_path = self.output_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                return {
                    "success": False,
                    "message": f"Authenticator for {service_name} already exists"
                }
            
            # Write the file
            file_path.write_text(code)
            self.logger.info(f"Generated authenticator for {service_name} at {file_path}")
            
            # Update __init__.py to import the new authenticator
            self._update_init_file(parameters['service_id'], parameters['service_class_name'])
            
            return {
                "success": True,
                "file_path": str(file_path),
                "message": f"Successfully created authenticator for {service_name}",
                "code": code,
                "requires_restart": True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating authenticator: {e}")
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}"
            }
    
    def _generate_with_claude(
        self,
        service_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate authenticator using Claude Code."""
        prompt = self._build_claude_prompt(service_name, parameters)
        
        try:
            # Call Claude Code CLI
            result = subprocess.run(
                ["claude", "code", "--prompt", prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Claude generation failed: {result.stderr}"
                }
            
            # Extract code from response
            code = self._extract_code_from_claude(result.stdout)
            
            if not code:
                return {
                    "success": False,
                    "message": "Could not extract valid code from Claude response"
                }
            
            # Validate generated code
            validation = self.validator.validate_full(code)
            if not validation["valid"]:
                return {
                    "success": False,
                    "message": f"Claude-generated code validation failed: {validation['errors']}",
                    "code": code,
                    "needs_review": True
                }
            
            # Save to file
            service_id = self._sanitize_service_id(service_name)
            filename = f"{service_id}_auth.py"
            file_path = self.output_dir / filename
            
            file_path.write_text(code)
            self.logger.info(f"Claude generated authenticator for {service_name}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "message": f"Claude successfully generated authenticator for {service_name}",
                "code": code,
                "requires_restart": True,
                "generated_by": "claude"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Claude generation timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Claude generation error: {str(e)}"
            }
    
    def _validate_parameters(
        self,
        template_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate parameters against template requirements."""
        template_data = self.metadata.get("templates", {}).get(template_type, {})
        required_fields = template_data.get("required_fields", [])
        
        missing_fields = []
        for field in required_fields:
            field_name = field["name"]
            if field_name not in parameters or not parameters[field_name]:
                missing_fields.append(field_name)
        
        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }
        
        return {"valid": True}
    
    def _sanitize_service_id(self, service_name: str) -> str:
        """Convert service name to valid Python identifier."""
        # Remove special characters and convert to lowercase
        service_id = re.sub(r'[^a-zA-Z0-9_]', '_', service_name.lower())
        # Remove leading numbers
        service_id = re.sub(r'^[0-9]+', '', service_id)
        # Remove duplicate underscores
        service_id = re.sub(r'_+', '_', service_id)
        return service_id.strip('_')
    
    def _to_class_name(self, service_name: str) -> str:
        """Convert service name to PascalCase class name."""
        # Remove special characters and split by spaces/underscores
        parts = re.sub(r'[^a-zA-Z0-9\s_]', '', service_name).split()
        # Capitalize each part and join
        return ''.join(word.capitalize() for word in parts)
    
    def _update_init_file(self, service_id: str, class_name: str):
        """Update authenticators/__init__.py to include new authenticator."""
        init_file = self.output_dir / "__init__.py"
        
        if not init_file.exists():
            # Create new init file
            content = f'''"""Authenticator modules."""

from .{service_id}_auth import {class_name}Authenticator

__all__ = ['{class_name}Authenticator']
'''
        else:
            content = init_file.read_text()
            
            # Add import statement
            import_line = f"from .{service_id}_auth import {class_name}Authenticator"
            if import_line not in content:
                # Find the last import line
                lines = content.split('\n')
                import_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('from .'):
                        import_index = i
                
                # Insert new import after last import
                lines.insert(import_index + 1, import_line)
                
                # Update __all__ list
                all_line = f"'{class_name}Authenticator'"
                for i, line in enumerate(lines):
                    if line.startswith('__all__'):
                        if all_line not in line:
                            # Add to __all__ list
                            lines[i] = lines[i].rstrip(']') + f", {all_line}]"
                        break
                
                content = '\n'.join(lines)
        
        init_file.write_text(content)
    
    def _build_claude_prompt(self, service_name: str, parameters: Dict[str, Any]) -> str:
        """Build prompt for Claude Code generation."""
        return f"""Create a Python authenticator class for {service_name}.

The authenticator should:
1. Inherit from BaseAuthenticator (import path: from base_authenticator import BaseAuthenticator)
2. Implement these required methods:
   - authenticate() -> bool: Perform authentication
   - verify_auth() -> bool: Check if authenticated
   - logout() -> bool: Logout/cleanup

Service details:
{json.dumps(parameters, indent=2)}

Requirements:
- Use self.credentials dict to access stored credentials
- Use self.logger for logging
- Call self.update_status() to update authentication status
- Use self.run_command() for CLI commands (returns tuple: success, stdout, stderr)
- Handle errors gracefully

Generate only the Python code for the authenticator class.
Include proper imports and docstrings.
"""
    
    def _extract_code_from_claude(self, response: str) -> Optional[str]:
        """Extract Python code from Claude's response."""
        # Look for code blocks
        code_pattern = r'```python\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # If no code blocks, try to extract from the response
        # Look for class definition
        if 'class ' in response and 'Authenticator' in response:
            lines = response.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                if line.startswith('import ') or line.startswith('from '):
                    in_code = True
                if in_code:
                    code_lines.append(line)
            
            if code_lines:
                return '\n'.join(code_lines)
        
        return None

    def test_authenticator(self, service_id: str) -> Dict[str, Any]:
        """Test a newly created authenticator."""
        try:
            # Import the authenticator module
            module_name = f"{service_id}_auth"
            module_path = self.output_dir / f"{module_name}.py"
            
            if not module_path.exists():
                return {
                    "success": False,
                    "message": f"Authenticator file not found: {module_path}"
                }
            
            # Read and validate the code
            code = module_path.read_text()
            validation = self.validator.validate_full(code)
            
            return {
                "success": validation["valid"],
                "validation": validation,
                "message": "Authenticator validation " + ("passed" if validation["valid"] else "failed")
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Test failed: {str(e)}"
            }