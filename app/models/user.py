"""
User model for authentication
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, user_id, username, email, password_hash=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"

