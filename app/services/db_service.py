"""
PostgreSQL Database Service
Handles user authentication and storage
"""

import psycopg2
from psycopg2 import pool
from flask import current_app
from werkzeug.security import generate_password_hash
from app.models.user import User


class DatabaseService:
    """Service for managing PostgreSQL connections and user operations"""
    
    def __init__(self):
        """Initialize database connection pool"""
        self.connection_pool = None
        self._init_pool()
        self._init_tables()
    
    def _init_pool(self):
        """Create connection pool"""
        try:
            # Build connection parameters
            conn_params = {
                'host': current_app.config["POSTGRES_HOST"],
                'port': current_app.config["POSTGRES_PORT"],
                'database': current_app.config["POSTGRES_DB"],
                'user': current_app.config["POSTGRES_USER"],
                'password': current_app.config["POSTGRES_PASSWORD"]
            }
            
            # Add SSL mode if specified (required for DigitalOcean)
            if current_app.config.get("POSTGRES_SSLMODE"):
                conn_params['sslmode'] = current_app.config["POSTGRES_SSLMODE"]
            
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                **conn_params
            )
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            raise
    
    def _init_tables(self):
        """Create users and knowledge_bases tables if they don't exist"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create knowledge_bases table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_bases (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(80) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, name)
                    )
                """)
                conn.commit()
        finally:
            self.connection_pool.putconn(conn)
    
    def create_user(self, username, email, password):
        """Create a new user"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (username, email, password_hash)
                )
                user_id = cursor.fetchone()[0]
                conn.commit()
                return User(user_id, username, email, password_hash)
        except psycopg2.IntegrityError:
            conn.rollback()
            return None
        finally:
            self.connection_pool.putconn(conn)
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE id = %s",
                    (user_id,)
                )
                row = cursor.fetchone()
                if row:
                    return User(row[0], row[1], row[2], row[3])
                return None
        finally:
            self.connection_pool.putconn(conn)
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE username = %s",
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    return User(row[0], row[1], row[2], row[3])
                return None
        finally:
            self.connection_pool.putconn(conn)
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE email = %s",
                    (email,)
                )
                row = cursor.fetchone()
                if row:
                    return User(row[0], row[1], row[2], row[3])
                return None
        finally:
            self.connection_pool.putconn(conn)
    
    def create_knowledge_base(self, user_id, name, description=""):
        """Create a new knowledge base for a user"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO knowledge_bases (user_id, name, description) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, name, description)
                )
                kb_id = cursor.fetchone()[0]
                conn.commit()
                return kb_id
        except psycopg2.IntegrityError:
            conn.rollback()
            return None
        finally:
            self.connection_pool.putconn(conn)
    
    def get_user_knowledge_bases(self, user_id):
        """Get all knowledge bases for a user"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, created_at FROM knowledge_bases WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,)
                )
                rows = cursor.fetchall()
                return [{
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                } for row in rows]
        finally:
            self.connection_pool.putconn(conn)
    
    def get_knowledge_base_by_id(self, kb_id, user_id):
        """Get a specific knowledge base by ID (verifies user ownership)"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, created_at FROM knowledge_bases WHERE id = %s AND user_id = %s",
                    (kb_id, user_id)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "created_at": row[3].isoformat() if row[3] else None
                    }
                return None
        finally:
            self.connection_pool.putconn(conn)
    
    def delete_knowledge_base(self, kb_id, user_id):
        """Delete a knowledge base (verifies user ownership)"""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM knowledge_bases WHERE id = %s AND user_id = %s",
                    (kb_id, user_id)
                )
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        finally:
            self.connection_pool.putconn(conn)
    
    def close(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()


# Singleton instance
_db_service = None


def get_db_service():
    """Get or create the database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

