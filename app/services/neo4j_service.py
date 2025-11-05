"""
Neo4j Database Service
Handles all Neo4j database connections and operations
"""

from neo4j import GraphDatabase
from flask import current_app


class Neo4jService:
    """Service for managing Neo4j database connections"""
    
    def __init__(self):
        """Initialize Neo4j driver"""
        self.driver = None
        self._connect()
        self._init_database()
    
    def _connect(self):
        """Establish connection to Neo4j"""
        uri = current_app.config["NEO4J_URI"]
        username = current_app.config["NEO4J_USERNAME"]
        password = current_app.config["NEO4J_PASSWORD"]
        self.database = current_app.config["NEO4J_DATABASE"]
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def _init_database(self):
        """Initialize database with constraints and indexes"""
        with self.driver.session(database=self.database) as session:
            # Create constraints for unique entities
            try:
                session.run("""
                    CREATE CONSTRAINT entity_name IF NOT EXISTS
                    FOR (e:Entity) REQUIRE e.name IS UNIQUE
                """)
            except Exception:
                pass  # Constraint might already exist
            
            # Create indexes for better query performance
            try:
                session.run("""
                    CREATE INDEX entity_type IF NOT EXISTS
                    FOR (e:Entity) ON (e.type)
                """)
            except Exception:
                pass  # Index might already exist
    
    def get_session(self):
        """Get a Neo4j session"""
        return self.driver.session(database=self.database)
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear all data from the database"""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")


# Singleton instance
_neo4j_service = None


def get_neo4j_service():
    """Get or create the Neo4j service instance"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service


