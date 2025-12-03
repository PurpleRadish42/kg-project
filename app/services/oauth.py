"""
Google OAuth service using Authlib
"""

from authlib.integrations.flask_client import OAuth
from flask import current_app
import os

oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
    
    # Register Google OAuth
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    return oauth

def get_google_oauth():
    """Get Google OAuth client"""
    return oauth.create_client('google')
