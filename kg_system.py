#!/usr/bin/env python3
"""
Knowledge Graph System for Context-Aware AI
Extracts information from natural language and stores it in Neo4j
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KnowledgeGraphSystem:
    def __init__(self):
        """Initialize the Knowledge Graph System with Neo4j and OpenAI connections"""
        # Neo4j connection
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # OpenAI connection
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # Using gpt-4o-mini (efficient and capable)
        
        # Initialize the database schema
        self._init_database()
    
    def _init_database(self):
        """Initialize database with constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints for unique entities
            session.run("""
                CREATE CONSTRAINT entity_name IF NOT EXISTS
                FOR (e:Entity) REQUIRE e.name IS UNIQUE
            """)
            
            # Create indexes for better query performance
            session.run("""
                CREATE INDEX entity_type IF NOT EXISTS
                FOR (e:Entity) ON (e.type)
            """)
    
    def extract_knowledge(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities, relationships, and temporal information from text using GPT-4o-mini
        """
        prompt = f"""You are an expert at extracting structured information from natural language text to build a knowledge graph.

Given the following text, extract:
1. All entities (people, objects, locations, etc.)
2. All relationships between entities
3. All properties of entities (color, model, etc.)
4. Temporal information (when things happened)
5. Location information (where things are/were)

Text: "{text}"

Return your response as a JSON object with the following structure:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "entity type (Person, Object, Location, etc.)",
      "properties": {{"key": "value"}}
    }}
  ],
  "relationships": [
    {{
      "source": "source entity name",
      "target": "target entity name",
      "type": "relationship type (LOCATED_AT, OWNS, MOVED_TO, etc.)",
      "properties": {{"key": "value"}},
      "timestamp": "when this happened (if specified, otherwise null)"
    }}
  ]
}}

Important guidelines:
- Track the CURRENT state of entities (where things ARE now, not just where they were)
- For temporal changes, create multiple relationships with timestamps
- Include properties like color, model, brand, etc. as entity properties
- Be specific about locations (e.g., "kitchen counter", "key hook by front door")
- Track who did what (e.g., "my roommate moved them")

Return ONLY the JSON object, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a knowledge extraction expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        knowledge = json.loads(content.strip())
        return knowledge
    
    def store_knowledge(self, knowledge: Dict[str, Any], source_text: str):
        """
        Store extracted knowledge in Neo4j with temporal and provenance metadata
        """
        with self.driver.session() as session:
            # Store provenance
            timestamp = datetime.now().isoformat()
            
            # Create entities
            for entity in knowledge.get("entities", []):
                session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type,
                        e.last_updated = $timestamp,
                        e.source = $source
                    WITH e
                    UNWIND $properties AS prop
                    SET e[prop.key] = prop.value
                """, 
                    name=entity["name"],
                    type=entity["type"],
                    timestamp=timestamp,
                    source=source_text[:100] + "...",
                    properties=[{"key": k, "value": v} for k, v in entity.get("properties", {}).items()]
                )
            
            # Create relationships
            for rel in knowledge.get("relationships", []):
                rel_timestamp = rel.get("timestamp") or timestamp
                
                session.run("""
                    MATCH (source:Entity {name: $source_name})
                    MATCH (target:Entity {name: $target_name})
                    MERGE (source)-[r:RELATES {type: $rel_type}]->(target)
                    SET r.timestamp = $timestamp,
                        r.created_at = $created_at,
                        r.source = $source
                    WITH r
                    UNWIND $properties AS prop
                    SET r[prop.key] = prop.value
                """,
                    source_name=rel["source"],
                    target_name=rel["target"],
                    rel_type=rel["type"],
                    timestamp=rel_timestamp,
                    created_at=timestamp,
                    source=source_text[:100] + "...",
                    properties=[{"key": k, "value": v} for k, v in rel.get("properties", {}).items()]
                )
    
    def query_knowledge(self, question: str) -> str:
        """
        Answer a question by querying the knowledge graph
        """
        # First, get relevant information from Neo4j
        with self.driver.session() as session:
            # Get all entities and relationships
            result = session.run("""
                MATCH (e:Entity)
                OPTIONAL MATCH (e)-[r:RELATES]->(target:Entity)
                RETURN e.name AS entity_name, 
                       e.type AS entity_type,
                       properties(e) AS entity_props,
                       r.type AS rel_type,
                       target.name AS target_name,
                       r.timestamp AS rel_timestamp,
                       properties(r) AS rel_props
                ORDER BY r.timestamp DESC
            """)
            
            graph_data = []
            for record in result:
                graph_data.append({
                    "entity": record["entity_name"],
                    "type": record["entity_type"],
                    "properties": record["entity_props"],
                    "relationship": record["rel_type"],
                    "target": record["target_name"],
                    "timestamp": record["rel_timestamp"],
                    "rel_properties": record["rel_props"]
                })
        
        # Format the graph data for GPT
        graph_context = json.dumps(graph_data, indent=2)
        
        # Use GPT to answer the question based on the graph data
        prompt = f"""You are answering questions based on a knowledge graph database.

Knowledge Graph Data:
{graph_context}

Question: {question}

Instructions:
- Answer based ONLY on the information in the knowledge graph
- Pay attention to timestamps - use the MOST RECENT information
- If something was moved or relocated, report its CURRENT location (most recent timestamp)
- Be specific and concise
- If the information is not in the knowledge graph, say "I don't have that information"

Answer:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on knowledge graph data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    def clear_database(self):
        """Clear all data from the database (useful for testing)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def close(self):
        """Close the Neo4j driver connection"""
        self.driver.close()


def main():
    """Main function to test the system"""
    
    # Initialize the system
    print("Initializing Knowledge Graph System...")
    kg = KnowledgeGraphSystem()
    
    # Clear existing data for fresh start
    print("Clearing existing data...")
    kg.clear_database()
    
    # Test paragraph
    paragraph = """On Monday morning, I placed my car keys on the kitchen counter next to the coffee maker. Later that afternoon, my roommate moved them to the key hook by the front door because he needed to use the car. The coffee maker is a Breville model that I bought in January 2024, and it's usually kept plugged in on the left side of the counter. My car is a blue Honda Civic parked in the garage, and I typically drive it to work every weekday. The front door key hook was installed by my roommate last month specifically for keeping keys organized. On Tuesday evening, the keys were missing from the hook, and I found them in my roommate's jacket pocket in the bedroom closet."""
    
    print("\n" + "="*80)
    print("PROCESSING TEXT")
    print("="*80)
    print(f"\n{paragraph}\n")
    
    # Extract and store knowledge
    print("Extracting knowledge from text...")
    knowledge = kg.extract_knowledge(paragraph)
    
    print(f"\nExtracted {len(knowledge.get('entities', []))} entities and {len(knowledge.get('relationships', []))} relationships")
    
    print("\nStoring knowledge in Neo4j...")
    kg.store_knowledge(knowledge, paragraph)
    print("✓ Knowledge stored successfully!")
    
    # Test questions
    questions = [
        "Where are my car keys?",
        "Where is the coffee maker?",
        "What's in the bedroom closet?",
        "What items are on the kitchen counter?"
    ]
    
    print("\n" + "="*80)
    print("ANSWERING QUESTIONS")
    print("="*80)
    
    for question in questions:
        print(f"\nQ: {question}")
        answer = kg.query_knowledge(question)
        print(f"A: {answer}")
    
    # Close connection
    kg.close()
    print("\n" + "="*80)
    print("Done!")
    print("="*80)


if __name__ == "__main__":
    main()

