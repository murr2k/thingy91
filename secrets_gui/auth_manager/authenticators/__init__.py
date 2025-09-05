"""Authenticator modules."""

# Import existing authenticators
from .github_auth import GitHubAuthenticator
from .fly_auth import FlyAuthenticator
from .cloudflare_auth import CloudflareAuthenticator
from .npm_auth import NPMAuthenticator

__all__ = [
    'GitHubAuthenticator',
    'FlyAuthenticator',
    'CloudflareAuthenticator',
    'NPMAuthenticator'
]