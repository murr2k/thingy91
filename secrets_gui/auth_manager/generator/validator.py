#!/usr/bin/env python3
"""
Authenticator Validator
Validates generated authenticator code for syntax and structure.
"""

import ast
import re
from typing import Dict, Any, List

class AuthenticatorValidator:
    """Validator for authenticator code."""
    
    def __init__(self):
        self.required_methods = ['authenticate', 'verify_auth', 'logout']
        self.required_base_class = 'BaseAuthenticator'
        self.dangerous_imports = [
            'os.system',
            'subprocess.call',
            'eval',
            'exec',
            '__import__'
        ]
    
    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error at line {e.lineno}: {e.msg}"
            }
    
    def validate_structure(self, code: str) -> Dict[str, Any]:
        """Validate authenticator structure and required methods."""
        try:
            tree = ast.parse(code)
            
            # Find class definition
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            if not classes:
                return {
                    "valid": False,
                    "error": "No class definition found"
                }
            
            authenticator_class = None
            for cls in classes:
                # Check if inherits from BaseAuthenticator
                for base in cls.bases:
                    if isinstance(base, ast.Name) and base.id == self.required_base_class:
                        authenticator_class = cls
                        break
            
            if not authenticator_class:
                return {
                    "valid": False,
                    "error": f"No class inheriting from {self.required_base_class} found"
                }
            
            # Check for required methods
            methods = [node.name for node in authenticator_class.body 
                      if isinstance(node, ast.FunctionDef)]
            
            missing_methods = []
            for required_method in self.required_methods:
                if required_method not in methods:
                    missing_methods.append(required_method)
            
            if missing_methods:
                return {
                    "valid": False,
                    "error": "Missing required methods",
                    "missing_methods": missing_methods
                }
            
            return {
                "valid": True,
                "class_name": authenticator_class.name,
                "methods": methods
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Structure validation error: {str(e)}"
            }
    
    def validate_security(self, code: str) -> Dict[str, Any]:
        """Check for security issues in the code."""
        issues = []
        
        # Check for dangerous imports
        for dangerous in self.dangerous_imports:
            if dangerous in code:
                issues.append(f"Dangerous import/call found: {dangerous}")
        
        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*["\'].*["\']',
            r'token\s*=\s*["\'].*["\']',
            r'api_key\s*=\s*["\'].*["\']',
            r'secret\s*=\s*["\'].*["\']'
        ]
        
        for pattern in credential_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append("Possible hardcoded credential found")
                break
        
        # Check for file system operations outside safe paths
        unsafe_patterns = [
            r'open\s*\(\s*["\']/',  # Opening absolute paths
            r'Path\s*\(\s*["\']/',  # Path with absolute paths
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, code):
                # Allow certain safe paths
                if not any(safe in code for safe in ['/home/', '~/']):
                    issues.append("Unsafe file system operation detected")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_imports(self, code: str) -> Dict[str, Any]:
        """Validate import statements."""
        try:
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
            
            # Check for required imports
            has_base_import = any('base_authenticator' in imp or 'BaseAuthenticator' in imp 
                                 for imp in imports)
            
            if not has_base_import:
                return {
                    "valid": False,
                    "error": "Missing import for BaseAuthenticator"
                }
            
            return {
                "valid": True,
                "imports": imports
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Import validation error: {str(e)}"
            }
    
    def validate_full(self, code: str) -> Dict[str, Any]:
        """Perform full validation of authenticator code."""
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Syntax check
        syntax_check = self.validate_syntax(code)
        if not syntax_check["valid"]:
            results["valid"] = False
            results["errors"].append(f"Syntax: {syntax_check['error']}")
            # Can't continue with other checks if syntax is invalid
            return results
        
        # Structure check
        structure_check = self.validate_structure(code)
        if not structure_check["valid"]:
            results["valid"] = False
            results["errors"].append(f"Structure: {structure_check['error']}")
            if "missing_methods" in structure_check:
                results["errors"].append(f"Missing methods: {', '.join(structure_check['missing_methods'])}")
        else:
            results["class_name"] = structure_check.get("class_name")
            results["methods"] = structure_check.get("methods")
        
        # Import check
        import_check = self.validate_imports(code)
        if not import_check["valid"]:
            results["valid"] = False
            results["errors"].append(f"Imports: {import_check['error']}")
        else:
            results["imports"] = import_check.get("imports")
        
        # Security check
        security_check = self.validate_security(code)
        if not security_check["valid"]:
            # Security issues are warnings, not errors
            results["warnings"].extend(security_check["issues"])
        
        return results
    
    def suggest_fixes(self, code: str, validation_result: Dict[str, Any]) -> List[str]:
        """Suggest fixes for validation issues."""
        suggestions = []
        
        if not validation_result["valid"]:
            for error in validation_result.get("errors", []):
                if "Missing import" in error:
                    suggestions.append(
                        "Add: from base_authenticator import BaseAuthenticator"
                    )
                elif "Missing methods" in error:
                    missing = validation_result.get("missing_methods", [])
                    for method in missing:
                        suggestions.append(
                            f"Add method: def {method}(self) -> bool:"
                        )
                elif "No class inheriting" in error:
                    suggestions.append(
                        "Ensure your class inherits from BaseAuthenticator"
                    )
        
        for warning in validation_result.get("warnings", []):
            if "hardcoded credential" in warning:
                suggestions.append(
                    "Use self.credentials dict instead of hardcoding credentials"
                )
            elif "Dangerous import" in warning:
                suggestions.append(
                    "Use self.run_command() instead of direct subprocess/os.system calls"
                )
        
        return suggestions