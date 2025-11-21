"""
Knowledge Graph Service
Handles knowledge extraction, storage, and querying
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from openai import OpenAI
from flask import current_app
from app.services.neo4j_service import get_neo4j_service


class KnowledgeGraphService:
    """Service for knowledge graph operations"""
    
    def __init__(self):
        """Initialize the Knowledge Graph Service"""
        self.neo4j = get_neo4j_service()
        self.client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
        self.model = current_app.config["OPENAI_MODEL"]
    
    def extract_knowledge(self, text: str) -> Dict[str, Any]:
        """
        Extract entities, relationships, and temporal information from text using GPT
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
      "type": "relationship type (LOCATED_AT, LOCATED_IN, CONTAINS, OWNS, MOVED_TO, etc.)",
      "properties": {{"key": "value"}},
      "timestamp": "when this happened (if specified, otherwise null)"
    }}
  ]
}}

Important guidelines:
- Track the CURRENT state of entities (where things ARE now, not just where they were)
- For temporal changes, create multiple relationships with timestamps
- **CRITICAL: Extract WHEN events happened** - "bought on Wednesday", "moved on Friday", etc.
- Include properties like color, model, brand, etc. as entity properties
- **Add temporal properties to entities**: If something was bought/created/moved at a specific time, add a property like "purchased_on": "Last Wednesday"
- Be specific about locations (e.g., "kitchen counter", "key hook by front door")
- Track who did what (e.g., "my roommate moved them")
- **CRITICAL: Create nested location relationships!** 
  Example: If "keys in jacket pocket in closet", create:
  1. keys LOCATED_IN jacket pocket
  2. jacket (or jacket pocket) LOCATED_IN bedroom closet
  3. bedroom closet CONTAINS jacket
- Use LOCATED_IN for containment (something inside something else)
- Use CONTAINS for the reverse (a location contains items)
- Always create BOTH directions when something is inside something else
- **For actions/events, create relationships with clear timestamps**: "bought on Last Wednesday", "watered on Thursday", etc.

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
    
    def store_knowledge(self, knowledge: Dict[str, Any], source_text: str, user_id: str = "demo_user"):
        """
        Store extracted knowledge in Neo4j with temporal and provenance metadata
        User-specific storage using user_id
        """
        with self.neo4j.get_session() as session:
            # Store provenance
            timestamp = datetime.now().isoformat()
            
            # Create Document node to store the full source text
            session.run("""
                CREATE (d:Document {
                    text: $text,
                    user_id: $user_id,
                    timestamp: $timestamp
                })
            """,
                text=source_text,
                user_id=user_id,
                timestamp=timestamp
            )
            
            # Create entities with user_id
            for entity in knowledge.get("entities", []):
                # First, create or update the entity
                session.run("""
                    MERGE (e:Entity {name: $name, user_id: $user_id})
                    SET e.type = $type,
                        e.last_updated = $timestamp,
                        e.source = $source
                """, 
                    name=entity["name"],
                    user_id=user_id,
                    type=entity["type"],
                    timestamp=timestamp,
                    source=source_text[:100] + "..."
                )
                
                # Then set properties separately to avoid issues
                for key, value in entity.get("properties", {}).items():
                    try:
                        session.run("""
                            MATCH (e:Entity {name: $name, user_id: $user_id})
                            SET e[$prop_key] = $prop_value
                        """, 
                            name=entity["name"],
                            user_id=user_id,
                            prop_key=key,
                            prop_value=value
                        )
                    except Exception as e:
                        print(f"Warning: Could not set property {key} for entity {entity['name']}: {e}")
                        pass
            
            # Create relationships with user_id
            for rel in knowledge.get("relationships", []):
                rel_timestamp = rel.get("timestamp") or timestamp
                
                session.run("""
                    MATCH (source:Entity {name: $source_name, user_id: $user_id})
                    MATCH (target:Entity {name: $target_name, user_id: $user_id})
                    MERGE (source)-[r:RELATES {type: $rel_type, user_id: $user_id}]->(target)
                    SET r.timestamp = $timestamp,
                        r.created_at = $created_at,
                        r.source = $source
                    WITH r
                    UNWIND $properties AS prop
                    SET r[prop.key] = prop.value
                """,
                    source_name=rel["source"],
                    target_name=rel["target"],
                    user_id=user_id,
                    rel_type=rel["type"],
                    timestamp=rel_timestamp,
                    created_at=timestamp,
                    source=source_text[:100] + "...",
                    properties=[{"key": k, "value": v} for k, v in rel.get("properties", {}).items()]
                )
    
    def query_knowledge(self, question: str, user_id: str = "demo_user") -> str:
        """
        Answer a question by querying the knowledge graph
        User-specific querying using user_id
        """
        # Get relevant information from Neo4j for this user
        with self.neo4j.get_session() as session:
            # Get all entities and direct relationships for this user
            result = session.run("""
                MATCH (e:Entity {user_id: $user_id})
                OPTIONAL MATCH (e)-[r:RELATES {user_id: $user_id}]->(target:Entity {user_id: $user_id})
                RETURN e.name AS entity_name, 
                       e.type AS entity_type,
                       properties(e) AS entity_props,
                       r.type AS rel_type,
                       target.name AS target_name,
                       r.timestamp AS rel_timestamp,
                       properties(r) AS rel_props
                ORDER BY r.timestamp DESC
            """, user_id=user_id)
            
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
            
            # Also get nested/transitive relationships (2-3 hops) for this user
            result = session.run("""
                MATCH path = (item:Entity {user_id: $user_id})-[r1:RELATES*1..3]->(location:Entity {user_id: $user_id})
                WHERE location.type = 'Location'
                WITH item, location, path, relationships(path) as rels, 
                     [r in relationships(path) | r.timestamp] as timestamps
                RETURN item.name AS item_name,
                       item.type AS item_type,
                       location.name AS location_name,
                       [r in rels | r.type] AS relationship_chain,
                       timestamps,
                       length(path) AS hops
                ORDER BY timestamps[-1] DESC
            """, user_id=user_id)
            
            nested_data = []
            for record in result:
                nested_data.append({
                    "item": record["item_name"],
                    "item_type": record["item_type"],
                    "location": record["location_name"],
                    "relationship_chain": record["relationship_chain"],
                    "timestamps": record["timestamps"],
                    "hops": record["hops"]
                })
        
        # Format the graph data for GPT
        graph_context = json.dumps({
            "direct_relationships": graph_data,
            "nested_relationships": nested_data
        }, indent=2)
        
        # Use GPT to answer the question based on the graph data
        prompt = f"""You are answering questions based on a knowledge graph database.

Knowledge Graph Data:
{graph_context}

Question: {question}

Instructions:
- Answer based ONLY on the information in the knowledge graph
- Pay attention to timestamps - use the MOST RECENT information
- If something was moved or relocated, report its CURRENT location (most recent timestamp)
- Use both direct_relationships AND nested_relationships to find answers
- For "What's in X?" questions, look for items that have X as their location (directly or nested)
- For "Where is X?" questions, find the most recent location of X
- **For "When did X happen?" questions**: Look for timestamps in relationships AND entity properties
- **Check entity properties** for temporal information like "purchased_on", "created_on", "moved_on", etc.
- **Check relationship timestamps** for when events occurred
- Look at relationship types like "BOUGHT", "PURCHASED", "MOVED_TO" for temporal events
- Be specific and concise
- If the information is not in the knowledge graph, say "I don't have that information"

Answer:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on knowledge graph data. You understand nested relationships."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    def get_all_entities(self, user_id: str = "demo_user") -> List[Dict]:
        """Get all entities from the knowledge graph for a specific user"""
        with self.neo4j.get_session() as session:
            result = session.run("""
                MATCH (e:Entity {user_id: $user_id})
                RETURN e.name AS name, e.type AS type, properties(e) AS properties
                ORDER BY e.type, e.name
            """, user_id=user_id)
            return [{"name": record["name"], "type": record["type"], "properties": record["properties"]} 
                    for record in result]
    
    def get_all_relationships(self, user_id: str = "demo_user") -> List[Dict]:
        """Get all relationships from the knowledge graph for a specific user"""
        with self.neo4j.get_session() as session:
            result = session.run("""
                MATCH (source:Entity {user_id: $user_id})-[r:RELATES {user_id: $user_id}]->(target:Entity {user_id: $user_id})
                RETURN source.name AS source,
                       r.type AS rel_type,
                       target.name AS target,
                       r.timestamp AS timestamp,
                       properties(r) AS properties
                ORDER BY r.timestamp DESC
            """, user_id=user_id)
            return [{
                "source": record["source"],
                "type": record["rel_type"],
                "target": record["target"],
                "timestamp": record["timestamp"],
                "properties": record["properties"]
            } for record in result]

    def clear_database(self, user_id: str = "demo_user"):
        """Clear all data for a specific user"""
        with self.neo4j.get_session() as session:
            session.run("""
                MATCH (n:Entity {user_id: $user_id})
                DETACH DELETE n
            """, user_id=user_id)
            
            # Also delete Document nodes for this user
            session.run("""
                MATCH (d:Document {user_id: $user_id})
                DELETE d
            """, user_id=user_id)
    
    def get_knowledge_base(self, user_id: str = "demo_user") -> List[Dict]:
        """Get all stored knowledge paragraphs for a specific user"""
        with self.neo4j.get_session() as session:
            result = session.run("""
                MATCH (d:Document {user_id: $user_id})
                RETURN d.text AS text, d.timestamp AS timestamp
                ORDER BY d.timestamp DESC
            """, user_id=user_id)
            return [{
                "text": record["text"],
                "timestamp": record["timestamp"]
            } for record in result]
    
    def generate_interactive_graph(self, user_id: str = "demo_user") -> str:
        """Generate an interactive graph visualization using Pyvis"""
        from pyvis.network import Network
        import networkx as nx
        
        # Create NetworkX graph
        G = nx.Graph()
        
        # Get entities and relationships
        entities = self.get_all_entities(user_id=user_id)
        relationships = self.get_all_relationships(user_id=user_id)
        
        # Add nodes
        for entity in entities:
            G.add_node(entity["name"], 
                      title=f"{entity['name']}\nType: {entity['type']}", 
                      type=entity["type"])
        
        # Add edges
        for rel in relationships:
            G.add_edge(rel["source"], rel["target"], 
                      title=rel["type"], 
                      label=rel["type"])
        
        # Create Pyvis network
        net = Network(height="600px", width="100%", bgcolor="#f5f3ef", font_color="#2c2416")
        
        # Configure physics for better interactivity
        net.set_options("""
        {
          "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 3,
            "color": {
              "border": "#2c2416",
              "background": "#ffffff",
              "highlight": {
                "border": "#d46a38",
                "background": "#fef5f0"
              }
            },
            "font": {
              "color": "#2c2416",
              "size": 14,
              "face": "Tiempos Text, serif"
            },
            "shape": "dot",
            "size": 25
          },
          "edges": {
            "color": {
              "color": "#2c2416",
              "highlight": "#d46a38"
            },
            "font": {
              "color": "#2c2416",
              "size": 12,
              "face": "Inter, sans-serif"
            },
            "smooth": {
              "type": "continuous"
            },
            "width": 2
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 150,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "stabilization": {
              "iterations": 200
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
          }
        }
        """)
        
        # Convert NetworkX graph to Pyvis
        net.from_nx(G)
        
        # Generate HTML
        html = net.generate_html()
        
        return html




