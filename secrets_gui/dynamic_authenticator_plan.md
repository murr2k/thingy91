# Dynamic Authenticator Creation System - Implementation Plan

## Executive Summary

This document outlines a system for dynamically creating new service authenticators through the Auth Manager GUI, with optional Claude Code CLI integration for complex authentication patterns.

## Architecture Overview

```
┌─────────────────┐     WebSocket      ┌─────────────────────┐
│   GUI (Docker)  │◄──────────────────►│  Auth Server (Host) │
│  - Request Form │                     │  - Generator Engine │
│  - Templates UI │                     │  - Template System  │
└─────────────────┘                     │  - Claude Code API  │
                                        └─────────────────────┘
                                                   │
                                                   ▼
                                        ┌─────────────────────┐
                                        │  New Authenticator  │
                                        │   Python Module     │
                                        └─────────────────────┘
```

## 1. Authenticator Template System

### 1.1 Base Templates

#### CLI Token Template
```python
class {ServiceName}Authenticator(BaseAuthenticator):
    """Auto-generated authenticator for {service_name}"""
    
    def __init__(self, credentials: dict):
        super().__init__("{service_id}", credentials)
        self.cli_command = "{cli_command}"
        self.token_env_var = "{token_env_var}"
        self.required_keys = ["{credential_key}"]
    
    def authenticate(self) -> bool:
        token = self.credentials.get("{credential_key}")
        if not token:
            return False
        
        # Standard CLI authentication pattern
        success, stdout, stderr = self.run_command(
            [self.cli_command, "auth", "login"],
            env={self.token_env_var: token}
        )
        return success
    
    def verify_auth(self) -> bool:
        # Standard CLI verification pattern
        success, _, _ = self.run_command(
            [self.cli_command, "auth", "status"]
        )
        return success
```

#### API Key Template
```python
class {ServiceName}Authenticator(BaseAuthenticator):
    """Auto-generated API authenticator for {service_name}"""
    
    def __init__(self, credentials: dict):
        super().__init__("{service_id}", credentials)
        self.api_endpoint = "{api_endpoint}"
        self.api_key_header = "{api_key_header}"
        self.required_keys = ["{credential_key}"]
    
    def authenticate(self) -> bool:
        api_key = self.credentials.get("{credential_key}")
        if not api_key:
            return False
        
        # Test API authentication
        import requests
        response = requests.get(
            f"{self.api_endpoint}/verify",
            headers={self.api_key_header: api_key}
        )
        return response.status_code == 200
```

#### Config File Template
```python
class {ServiceName}Authenticator(BaseAuthenticator):
    """Auto-generated config-based authenticator for {service_name}"""
    
    def __init__(self, credentials: dict):
        super().__init__("{service_id}", credentials)
        self.config_path = Path.home() / "{config_path}"
        self.required_keys = ["{credential_key}"]
    
    def authenticate(self) -> bool:
        token = self.credentials.get("{credential_key}")
        if not token:
            return False
        
        # Write configuration
        config = {config_template}
        self.config_path.parent.mkdir(exist_ok=True)
        self.config_path.write_text(json.dumps(config))
        return True
```

### 1.2 Template Metadata

```yaml
templates:
  cli_token:
    name: "CLI with Token"
    description: "For CLIs that accept tokens via environment variables"
    required_fields:
      - cli_command: "CLI executable name"
      - token_env_var: "Environment variable name"
      - credential_key: "Key in secrets store"
    examples:
      - "GitHub CLI (gh)"
      - "Vercel CLI"
    
  api_key:
    name: "API with Key"
    description: "For REST APIs with key-based authentication"
    required_fields:
      - api_endpoint: "Base API URL"
      - api_key_header: "Header name for API key"
      - credential_key: "Key in secrets store"
    examples:
      - "OpenAI API"
      - "Stripe API"
    
  config_file:
    name: "Configuration File"
    description: "For tools that read credentials from config files"
    required_fields:
      - config_path: "Path to config file"
      - config_template: "JSON structure template"
      - credential_key: "Key in secrets store"
    examples:
      - "AWS CLI"
      - "Google Cloud SDK"
```

## 2. Authenticator Generator Service

### 2.1 Core Generator Class

```python
class AuthenticatorGenerator:
    def __init__(self):
        self.templates_dir = Path("auth_manager/templates")
        self.output_dir = Path("auth_manager/authenticators")
        self.claude_enabled = self.check_claude_availability()
    
    def generate_authenticator(
        self,
        service_name: str,
        template_type: str,
        parameters: dict,
        use_claude: bool = False
    ) -> dict:
        """
        Generate a new authenticator module.
        
        Returns:
            dict: {
                "success": bool,
                "file_path": str,
                "message": str,
                "code": str (if success)
            }
        """
        if use_claude and self.claude_enabled:
            return self.generate_with_claude(service_name, parameters)
        else:
            return self.generate_from_template(
                service_name, 
                template_type, 
                parameters
            )
    
    def generate_from_template(
        self,
        service_name: str,
        template_type: str,
        parameters: dict
    ) -> dict:
        """Generate authenticator from predefined template"""
        # Load template
        template = self.load_template(template_type)
        
        # Validate parameters
        validation = self.validate_parameters(template_type, parameters)
        if not validation["valid"]:
            return {"success": False, "message": validation["error"]}
        
        # Generate code
        code = self.render_template(template, service_name, parameters)
        
        # Save to file
        filename = f"{service_name.lower()}_auth.py"
        file_path = self.output_dir / filename
        
        # Test syntax
        if not self.validate_python_syntax(code):
            return {"success": False, "message": "Generated code has syntax errors"}
        
        # Save file
        file_path.write_text(code)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "message": f"Authenticator created for {service_name}",
            "code": code
        }
    
    def generate_with_claude(
        self,
        service_name: str,
        parameters: dict
    ) -> dict:
        """Generate authenticator using Claude Code CLI"""
        prompt = self.build_claude_prompt(service_name, parameters)
        
        # Call Claude Code CLI
        result = subprocess.run(
            ["claude", "code", "--prompt", prompt],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse and validate generated code
            code = self.extract_code_from_response(result.stdout)
            
            # Additional validation
            if self.validate_authenticator_code(code):
                # Save to file
                filename = f"{service_name.lower()}_auth.py"
                file_path = self.output_dir / filename
                file_path.write_text(code)
                
                return {
                    "success": True,
                    "file_path": str(file_path),
                    "message": f"Claude generated authenticator for {service_name}",
                    "code": code
                }
        
        return {
            "success": False,
            "message": "Claude generation failed or produced invalid code"
        }
```

### 2.2 Claude Code Integration

```python
class ClaudeAuthenticatorGenerator:
    """Integration with Claude Code CLI for complex authenticators"""
    
    def build_claude_prompt(self, service_info: dict) -> str:
        return f"""
        Create a Python authenticator class for {service_info['name']}.
        
        Requirements:
        - Inherit from BaseAuthenticator (already imported)
        - Service ID: {service_info['service_id']}
        - Authentication method: {service_info['auth_method']}
        - Documentation: {service_info['docs_url']}
        
        Authentication details:
        {service_info.get('auth_details', 'N/A')}
        
        The authenticator should:
        1. Implement authenticate() method to log in
        2. Implement verify_auth() method to check status
        3. Implement logout() method to clean up
        4. Handle errors gracefully
        5. Use self.logger for logging
        6. Update status with self.update_status()
        
        Base class provides:
        - self.run_command() for CLI commands
        - self.credentials dict with secrets
        - self.logger for logging
        
        Generate only the Python class code, no explanations.
        """
    
    def validate_authenticator_code(self, code: str) -> bool:
        """Validate generated authenticator meets requirements"""
        required_methods = ['authenticate', 'verify_auth', 'logout']
        required_imports = ['BaseAuthenticator']
        
        # Check for required methods
        for method in required_methods:
            if f"def {method}(" not in code:
                return False
        
        # Check for base class
        if "BaseAuthenticator" not in code:
            return False
        
        # Syntax check
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
```

## 3. WebSocket Protocol Extensions

### 3.1 New Message Types

```python
# Request: Create new authenticator
{
    "action": "create_authenticator",
    "service_name": "Vercel",
    "template_type": "cli_token",
    "parameters": {
        "cli_command": "vercel",
        "token_env_var": "VERCEL_TOKEN",
        "credential_key": "VERCEL_AUTH_TOKEN"
    },
    "use_claude": false
}

# Response: Authenticator created
{
    "type": "authenticator_created",
    "data": {
        "success": true,
        "service_id": "vercel",
        "file_path": "/auth_manager/authenticators/vercel_auth.py",
        "message": "Authenticator created successfully",
        "requires_restart": true
    }
}

# Request: List available templates
{
    "action": "list_templates"
}

# Response: Template list
{
    "type": "template_list",
    "data": {
        "templates": [
            {
                "id": "cli_token",
                "name": "CLI with Token",
                "description": "...",
                "required_fields": [...]
            }
        ]
    }
}

# Request: Test new authenticator
{
    "action": "test_authenticator",
    "service_id": "vercel"
}

# Response: Test results
{
    "type": "test_results",
    "data": {
        "success": true,
        "authenticate": true,
        "verify": true,
        "logout": true,
        "errors": []
    }
}
```

## 4. GUI Implementation

### 4.1 UI Components

#### Add Service Button
- Location: Dashboard header
- Icon: Plus sign
- Action: Opens modal dialog

#### New Authenticator Modal
```html
<div class="modal" id="newAuthModal">
    <h2>Add New Service</h2>
    
    <!-- Step 1: Basic Info -->
    <div class="step" id="step1">
        <input type="text" id="serviceName" placeholder="Service Name (e.g., Vercel)">
        <input type="text" id="serviceDescription" placeholder="Description">
        <button onclick="nextStep()">Next</button>
    </div>
    
    <!-- Step 2: Template Selection -->
    <div class="step" id="step2">
        <h3>Select Authentication Type</h3>
        <div class="template-cards">
            <div class="template-card" data-template="cli_token">
                <h4>CLI with Token</h4>
                <p>For command-line tools that use tokens</p>
            </div>
            <div class="template-card" data-template="api_key">
                <h4>API with Key</h4>
                <p>For REST APIs with key authentication</p>
            </div>
            <div class="template-card" data-template="config_file">
                <h4>Configuration File</h4>
                <p>For tools that read from config files</p>
            </div>
            <div class="template-card" data-template="custom">
                <h4>Custom (Claude)</h4>
                <p>Let Claude Code create it for you</p>
            </div>
        </div>
    </div>
    
    <!-- Step 3: Parameters -->
    <div class="step" id="step3">
        <h3>Configuration</h3>
        <div id="dynamicFields">
            <!-- Dynamically populated based on template -->
        </div>
        <button onclick="createAuthenticator()">Create</button>
    </div>
    
    <!-- Step 4: Claude Input (if custom) -->
    <div class="step" id="step4">
        <h3>Describe Authentication Process</h3>
        <textarea id="authDescription" rows="10">
            How does authentication work for this service?
            Include:
            - CLI commands or API endpoints
            - Where credentials are stored
            - How to verify authentication
            - Link to documentation
        </textarea>
        <button onclick="generateWithClaude()">Generate with Claude</button>
    </div>
</div>
```

### 4.2 JavaScript Functions

```javascript
async function createAuthenticator() {
    const serviceName = document.getElementById('serviceName').value;
    const template = getSelectedTemplate();
    const parameters = collectParameters();
    
    const request = {
        action: 'create_authenticator',
        service_name: serviceName,
        template_type: template,
        parameters: parameters,
        use_claude: template === 'custom'
    };
    
    const response = await sendWebSocketRequest(request);
    
    if (response.success) {
        showSuccessMessage('Authenticator created! Restarting auth server...');
        setTimeout(() => {
            location.reload();
        }, 3000);
    } else {
        showError(response.message);
    }
}

function collectParameters() {
    const params = {};
    document.querySelectorAll('.parameter-field').forEach(field => {
        params[field.dataset.param] = field.value;
    });
    return params;
}
```

## 5. Security Considerations

### 5.1 Input Validation
- Sanitize service names (alphanumeric + underscore only)
- Validate URLs and endpoints
- Escape template parameters
- Limit file paths to safe directories

### 5.2 Code Execution Safety
- Syntax validation before saving
- Import restrictions (no os.system, subprocess without approval)
- Sandbox testing environment
- Manual review option for Claude-generated code

### 5.3 Credential Protection
- Never expose credentials in generated code
- Always use credentials dict from base class
- Validate credential keys exist before use
- Audit trail for new authenticator creation

## 6. Implementation Phases

### Phase 1: Template System (Week 1)
- [ ] Create template files for common patterns
- [ ] Build template renderer
- [ ] Add parameter validation
- [ ] Create generator service

### Phase 2: WebSocket Integration (Week 2)
- [ ] Add new WebSocket message handlers
- [ ] Implement authenticator creation endpoint
- [ ] Add template listing endpoint
- [ ] Create test endpoint

### Phase 3: GUI Components (Week 3)
- [ ] Design and implement modal UI
- [ ] Add template selection interface
- [ ] Create dynamic parameter forms
- [ ] Implement WebSocket client functions

### Phase 4: Claude Integration (Week 4)
- [ ] Create Claude prompt builder
- [ ] Implement CLI integration
- [ ] Add code validation
- [ ] Create review interface

### Phase 5: Testing & Polish (Week 5-6)
- [ ] Test with various services
- [ ] Add error handling
- [ ] Create documentation
- [ ] Performance optimization

## 7. Example Use Cases

### Simple CLI Tool
**Service**: Vercel CLI
**Template**: cli_token
**Parameters**:
- cli_command: "vercel"
- token_env_var: "VERCEL_TOKEN"
- credential_key: "VERCEL_AUTH_TOKEN"

### API Service
**Service**: OpenAI
**Template**: api_key
**Parameters**:
- api_endpoint: "https://api.openai.com/v1"
- api_key_header: "Authorization"
- credential_key: "OPENAI_API_KEY"

### Complex Authentication
**Service**: Kubernetes
**Template**: custom (Claude)
**Description**: "Kubernetes CLI that uses kubeconfig file with certificates and context switching"

## 8. Benefits

1. **Rapid Service Integration**: Add new services in minutes
2. **No Coding Required**: Templates handle common patterns
3. **Claude for Complex Cases**: AI assistance for unique authentication flows
4. **Consistent Patterns**: All authenticators follow the same structure
5. **Hot Reload**: New authenticators available immediately
6. **GUI Management**: No need to touch code for simple services

## 9. Future Enhancements

- **Plugin Marketplace**: Share authenticators with community
- **Auto-discovery**: Detect installed CLIs and suggest authenticators
- **Credential Scanner**: Find and import existing credentials
- **Multi-step Auth**: Support for OAuth flows
- **Dependency Management**: Auto-install required Python packages
- **Version Control**: Track authenticator changes
- **Rollback**: Revert to previous authenticator versions

## 10. Technical Requirements

### Dependencies
- Python 3.8+
- WebSockets library
- Jinja2 (for templates)
- Claude Code CLI (optional)
- PyYAML (for template metadata)

### File Structure
```
auth_manager/
├── authenticators/
│   ├── __init__.py
│   ├── github_auth.py      (existing)
│   ├── flyio_auth.py       (existing)
│   └── vercel_auth.py      (generated)
├── templates/
│   ├── cli_token.py.j2
│   ├── api_key.py.j2
│   ├── config_file.py.j2
│   └── metadata.yaml
├── generator/
│   ├── __init__.py
│   ├── generator.py
│   ├── claude_integration.py
│   └── validator.py
└── websocket_server.py     (extended)
```

## Conclusion

This system would enable users to rapidly add support for new services without writing code. Simple services can use templates, while complex authentication flows can leverage Claude Code's capabilities. The entire process is managed through the GUI, making it accessible to non-developers while maintaining the flexibility needed for complex scenarios.

The implementation is modular and can be rolled out in phases, with the template system providing immediate value and Claude integration adding advanced capabilities later.