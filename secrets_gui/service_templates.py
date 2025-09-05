"""
Service Templates for Secrets Manager
Defines templates for common service types with their specific requirements
"""

# Service type templates with configurable fields
SERVICE_TEMPLATES = {
    'api_key': {
        'name': 'API Key Service',
        'description': 'Simple API key authentication',
        'icon_options': ['🔑', '🎫', '📋', '🔐'],
        'fields': [
            {
                'key': 'API_KEY',
                'label': 'API Key',
                'type': 'password',
                'required': True,
                'validation': 'min_length:32',
                'placeholder': 'Enter API key'
            },
            {
                'key': 'API_URL',
                'label': 'API Endpoint',
                'type': 'url',
                'required': False,
                'placeholder': 'https://api.example.com'
            }
        ],
        'health_check_options': [
            {
                'type': 'https',
                'name': 'HTTPS Health Check',
                'fields': ['endpoint', 'timeout', 'expected_status']
            },
            {
                'type': 'none',
                'name': 'No Health Check'
            }
        ]
    },
    
    'oauth2': {
        'name': 'OAuth 2.0 Service',
        'description': 'OAuth 2.0 client credentials',
        'icon_options': ['🔐', '🎟️', '🔓'],
        'fields': [
            {
                'key': 'CLIENT_ID',
                'label': 'Client ID',
                'type': 'text',
                'required': True,
                'placeholder': 'OAuth client ID'
            },
            {
                'key': 'CLIENT_SECRET',
                'label': 'Client Secret',
                'type': 'password',
                'required': True,
                'validation': 'min_length:16',
                'placeholder': 'OAuth client secret'
            },
            {
                'key': 'TOKEN_URL',
                'label': 'Token URL',
                'type': 'url',
                'required': True,
                'placeholder': 'https://auth.example.com/token'
            },
            {
                'key': 'SCOPE',
                'label': 'Scopes',
                'type': 'text',
                'required': False,
                'placeholder': 'read write admin'
            }
        ],
        'health_check_options': [
            {
                'type': 'oauth_token',
                'name': 'OAuth Token Test',
                'fields': ['token_url', 'timeout']
            }
        ]
    },
    
    'database': {
        'name': 'Database Connection',
        'description': 'Database connection credentials',
        'icon_options': ['🗄️', '💾', '🗃️', '📊'],
        'fields': [
            {
                'key': 'DB_HOST',
                'label': 'Host',
                'type': 'text',
                'required': True,
                'placeholder': 'localhost or IP address'
            },
            {
                'key': 'DB_PORT',
                'label': 'Port',
                'type': 'number',
                'required': True,
                'default': '5432',
                'placeholder': '5432'
            },
            {
                'key': 'DB_NAME',
                'label': 'Database Name',
                'type': 'text',
                'required': True,
                'placeholder': 'mydatabase'
            },
            {
                'key': 'DB_USER',
                'label': 'Username',
                'type': 'text',
                'required': True,
                'placeholder': 'dbuser'
            },
            {
                'key': 'DB_PASSWORD',
                'label': 'Password',
                'type': 'password',
                'required': True,
                'placeholder': 'Database password'
            },
            {
                'key': 'DB_SSL_MODE',
                'label': 'SSL Mode',
                'type': 'select',
                'options': ['disable', 'require', 'verify-ca', 'verify-full'],
                'default': 'require',
                'required': False
            }
        ],
        'health_check_options': [
            {
                'type': 'database',
                'name': 'Database Connection Test',
                'fields': ['driver', 'timeout']
            }
        ]
    },
    
    'cloud_provider': {
        'name': 'Cloud Provider',
        'description': 'Cloud service provider credentials',
        'icon_options': ['☁️', '🌩️', '⛅', '🌤️'],
        'subtypes': {
            'aws': {
                'name': 'AWS',
                'fields': [
                    {
                        'key': 'AWS_ACCESS_KEY_ID',
                        'label': 'Access Key ID',
                        'type': 'text',
                        'required': True,
                        'validation': 'regex:^AKIA[0-9A-Z]{16}$',
                        'placeholder': 'AKIAIOSFODNN7EXAMPLE'
                    },
                    {
                        'key': 'AWS_SECRET_ACCESS_KEY',
                        'label': 'Secret Access Key',
                        'type': 'password',
                        'required': True,
                        'validation': 'min_length:40',
                        'placeholder': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
                    },
                    {
                        'key': 'AWS_REGION',
                        'label': 'Region',
                        'type': 'select',
                        'options': ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
                        'required': True
                    }
                ]
            },
            'gcp': {
                'name': 'Google Cloud',
                'fields': [
                    {
                        'key': 'GCP_SERVICE_ACCOUNT',
                        'label': 'Service Account JSON',
                        'type': 'json',
                        'required': True,
                        'placeholder': 'Paste service account JSON'
                    }
                ]
            },
            'azure': {
                'name': 'Azure',
                'fields': [
                    {
                        'key': 'AZURE_CLIENT_ID',
                        'label': 'Client ID',
                        'type': 'text',
                        'required': True
                    },
                    {
                        'key': 'AZURE_CLIENT_SECRET',
                        'label': 'Client Secret',
                        'type': 'password',
                        'required': True
                    },
                    {
                        'key': 'AZURE_TENANT_ID',
                        'label': 'Tenant ID',
                        'type': 'text',
                        'required': True
                    },
                    {
                        'key': 'AZURE_SUBSCRIPTION_ID',
                        'label': 'Subscription ID',
                        'type': 'text',
                        'required': False
                    }
                ]
            }
        }
    },
    
    'messaging': {
        'name': 'Messaging Service',
        'description': 'Message queue or streaming service',
        'icon_options': ['📬', '📨', '💬', '📡'],
        'subtypes': {
            'kafka': {
                'name': 'Apache Kafka',
                'fields': [
                    {
                        'key': 'KAFKA_BROKERS',
                        'label': 'Broker List',
                        'type': 'text',
                        'required': True,
                        'placeholder': 'broker1:9092,broker2:9092'
                    },
                    {
                        'key': 'KAFKA_SASL_USERNAME',
                        'label': 'SASL Username',
                        'type': 'text',
                        'required': False
                    },
                    {
                        'key': 'KAFKA_SASL_PASSWORD',
                        'label': 'SASL Password',
                        'type': 'password',
                        'required': False
                    }
                ]
            },
            'rabbitmq': {
                'name': 'RabbitMQ',
                'fields': [
                    {
                        'key': 'RABBITMQ_URL',
                        'label': 'Connection URL',
                        'type': 'url',
                        'required': True,
                        'placeholder': 'amqp://user:pass@host:5672/vhost'
                    }
                ]
            },
            'redis': {
                'name': 'Redis',
                'fields': [
                    {
                        'key': 'REDIS_HOST',
                        'label': 'Host',
                        'type': 'text',
                        'required': True
                    },
                    {
                        'key': 'REDIS_PORT',
                        'label': 'Port',
                        'type': 'number',
                        'default': '6379',
                        'required': True
                    },
                    {
                        'key': 'REDIS_PASSWORD',
                        'label': 'Password',
                        'type': 'password',
                        'required': False
                    }
                ]
            }
        }
    },
    
    'custom': {
        'name': 'Custom Service',
        'description': 'Define your own service configuration',
        'icon_options': ['⚙️', '🔧', '🛠️', '📦'],
        'custom_fields': True,
        'fields': []  # User can add custom fields
    }
}

# Health check type definitions
HEALTH_CHECK_TYPES = {
    'https': {
        'name': 'HTTPS Endpoint',
        'fields': [
            {
                'key': 'endpoint',
                'label': 'Health Check URL',
                'type': 'url',
                'required': True,
                'placeholder': 'https://api.example.com/health'
            },
            {
                'key': 'timeout',
                'label': 'Timeout (seconds)',
                'type': 'number',
                'default': 5,
                'min': 1,
                'max': 30
            },
            {
                'key': 'expected_status',
                'label': 'Expected Status Code',
                'type': 'number',
                'default': 200
            }
        ]
    },
    'tcp': {
        'name': 'TCP Port Check',
        'fields': [
            {
                'key': 'host',
                'label': 'Host',
                'type': 'text',
                'required': True
            },
            {
                'key': 'port',
                'label': 'Port',
                'type': 'number',
                'required': True
            },
            {
                'key': 'timeout',
                'label': 'Timeout (seconds)',
                'type': 'number',
                'default': 5
            }
        ]
    },
    'command': {
        'name': 'Command Execution',
        'fields': [
            {
                'key': 'command',
                'label': 'Command',
                'type': 'text',
                'required': True,
                'placeholder': 'aws sts get-caller-identity'
            },
            {
                'key': 'timeout',
                'label': 'Timeout (seconds)',
                'type': 'number',
                'default': 10
            }
        ]
    },
    'database': {
        'name': 'Database Connection',
        'fields': [
            {
                'key': 'driver',
                'label': 'Database Driver',
                'type': 'select',
                'options': ['postgresql', 'mysql', 'mongodb', 'redis'],
                'required': True
            },
            {
                'key': 'timeout',
                'label': 'Timeout (seconds)',
                'type': 'number',
                'default': 5
            }
        ]
    },
    'oauth_token': {
        'name': 'OAuth Token Test',
        'fields': [
            {
                'key': 'token_url',
                'label': 'Token URL',
                'type': 'url',
                'required': True
            },
            {
                'key': 'timeout',
                'label': 'Timeout (seconds)',
                'type': 'number',
                'default': 10
            }
        ]
    },
    'none': {
        'name': 'No Health Check',
        'fields': []
    }
}

def get_template(template_type: str, subtype: str = None):
    """Get a service template by type and optional subtype"""
    template = SERVICE_TEMPLATES.get(template_type)
    if template and subtype and 'subtypes' in template:
        subtype_template = template['subtypes'].get(subtype)
        if subtype_template:
            # Merge base template with subtype
            merged = template.copy()
            merged.update(subtype_template)
            return merged
    return template

def validate_field(field_def: dict, value: str) -> tuple[bool, str]:
    """Validate a field value against its definition"""
    if field_def.get('required') and not value:
        return False, f"{field_def['label']} is required"
    
    if not value:
        return True, ""
    
    validation = field_def.get('validation', '')
    
    if 'min_length:' in validation:
        min_len = int(validation.split('min_length:')[1].split(',')[0])
        if len(value) < min_len:
            return False, f"{field_def['label']} must be at least {min_len} characters"
    
    if 'regex:' in validation:
        import re
        pattern = validation.split('regex:')[1]
        if not re.match(pattern, value):
            return False, f"{field_def['label']} format is invalid"
    
    if field_def.get('type') == 'url':
        if not value.startswith(('http://', 'https://')):
            return False, f"{field_def['label']} must be a valid URL"
    
    if field_def.get('type') == 'number':
        try:
            num = float(value)
            if 'min' in field_def and num < field_def['min']:
                return False, f"{field_def['label']} must be at least {field_def['min']}"
            if 'max' in field_def and num > field_def['max']:
                return False, f"{field_def['label']} must be at most {field_def['max']}"
        except ValueError:
            return False, f"{field_def['label']} must be a number"
    
    if field_def.get('type') == 'json':
        import json
        try:
            json.loads(value)
        except json.JSONDecodeError:
            return False, f"{field_def['label']} must be valid JSON"
    
    return True, ""