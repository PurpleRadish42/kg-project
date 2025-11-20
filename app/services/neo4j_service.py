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
        try:
            with self.driver.session(database=self.database) as session:
                # Drop old constraint if it exists (name only)
                try:
                    session.run("DROP CONSTRAINT entity_name IF EXISTS")
                except Exception:
                    pass  # Constraint might not exist
                
                # Create composite constraint for unique entities per user
                # This allows same entity name for different users
                try:
                    session.run("""
                        CREATE CONSTRAINT entity_name_user IF NOT EXISTS
                        FOR (e:Entity) REQUIRE (e.name, e.user_id) IS UNIQUE
                    """)
                except Exception as e:
                    error_msg = str(e).lower()
                    if "permission" in error_msg or "access" in error_msg or "forbidden" in error_msg:
                        print(f"\n⚠️  PERMISSIONS WARNING: Cannot create constraint - {e}")
                        print("   This is often a Neo4j Aura permissions issue.")
                        print("   The app will work, but constraints won't be enforced.")
                        print("   See NEO4J_PERMISSIONS_FIX.md for solutions.\n")
                    else:
                        print(f"Note: Could not create constraint: {e}")
                    pass
                
                # Create indexes for better query performance
                try:
                    session.run("""
                        CREATE INDEX entity_type IF NOT EXISTS
                        FOR (e:Entity) ON (e.type)
                    """)
                except Exception as e:
                    print(f"Note: Could not create type index: {e}")
                    pass
                
                # Create index on user_id for faster filtering
                try:
                    session.run("""
                        CREATE INDEX entity_user_id IF NOT EXISTS
                        FOR (e:Entity) ON (e.user_id)
                    """)
                except Exception as e:
                    print(f"Note: Could not create user_id index: {e}")
                    pass
        except Exception as e:
            error_msg = str(e).lower()
            if "permission" in error_msg or "access" in error_msg or "forbidden" in error_msg:
                print(f"\n❌ DATABASE ACCESS ERROR: {e}")
                print(f"   Database: {self.database}")
                print(f"   User: {current_app.config['NEO4J_USERNAME']}")
                print("\n   POSSIBLE SOLUTIONS:")
                print("   1. Check database name in .env (try different database)")
                print("   2. Grant permissions in Neo4j Aura dashboard")
                print("   3. Check your Neo4j Aura plan limits")
                print("   4. See NEO4J_PERMISSIONS_FIX.md for details\n")
                raise  # Re-raise so user knows about the issue
            else:
                print(f"Warning: Database initialization had issues: {e}")
                # Don't fail completely - app might still work
    
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


