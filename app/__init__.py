"""
Flask Application Factory
"""

from flask import Flask
from config import config


def create_app(config_name="default"):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from app.routes import api, web
    app.register_blueprint(web.bp)
    app.register_blueprint(api.bp, url_prefix="/api")
    
    return app


