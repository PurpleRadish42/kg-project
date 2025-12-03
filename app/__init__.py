"""
Flask Application Factory
"""

from flask import Flask
from flask_login import LoginManager
from config import config


login_manager = LoginManager()


def create_app(config_name="default"):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    
    # Initialize OAuth
    from app.services.oauth import init_oauth
    init_oauth(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.services.db_service import get_db_service
        db_service = get_db_service()
        return db_service.get_user_by_id(int(user_id))
    
    # Register blueprints
    from app.routes import api, web, auth
    app.register_blueprint(web.bp)
    app.register_blueprint(auth.bp, url_prefix="/auth")
    app.register_blueprint(api.bp, url_prefix="/api")
    
    return app


