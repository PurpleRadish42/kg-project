#!/usr/bin/env python3
"""
Diagnostic script to see what's actually stored in the Neo4j database
"""

from kg_system import KnowledgeGraphSystem
import json

def main():
    kg = KnowledgeGraphSystem()
    
    print("="*80)
    print("KNOWLEDGE GRAPH DIAGNOSTIC")
    print("="*80)
    
    with kg.driver.session() as session:
        # Get all entities
        print("\n--- ALL ENTITIES ---\n")
        result = session.run("""
            MATCH (e:Entity)
            RETURN e.name AS name, e.type AS type, properties(e) AS props
            ORDER BY e.type, e.name
        """)
        
        for record in result:
            print(f"• {record['name']} ({record['type']})")
            props = record['props']
            for key, value in props.items():
                if key not in ['name', 'type', 'last_updated', 'source']:
                    print(f"    - {key}: {value}")
        
        # Get all relationships
        print("\n--- ALL RELATIONSHIPS ---\n")
        result = session.run("""
            MATCH (source:Entity)-[r:RELATES]->(target:Entity)
            RETURN source.name AS source, 
                   r.type AS rel_type,
                   target.name AS target,
                   r.timestamp AS timestamp,
                   properties(r) AS props
            ORDER BY r.timestamp
        """)
        
        for record in result:
            timestamp = record['timestamp'] if record['timestamp'] else 'no timestamp'
            print(f"{record['source']} --[{record['rel_type']}]--> {record['target']}")
            print(f"    @ {timestamp}")
            props = record['props']
            for key, value in props.items():
                if key not in ['type', 'timestamp', 'created_at', 'source']:
                    print(f"    - {key}: {value}")
        
        # Check specific query: What's in bedroom closet?
        print("\n--- CHECKING: What's in the bedroom closet? ---\n")
        result = session.run("""
            MATCH (item:Entity)-[r:RELATES]->(loc:Entity)
            WHERE loc.name =~ '.*bedroom.*closet.*' OR loc.name =~ '.*closet.*'
            RETURN item.name AS item, r.type AS rel_type, loc.name AS location
        """)
        
        found = False
        for record in result:
            found = True
            print(f"Found: {record['item']} --[{record['rel_type']}]--> {record['location']}")
        
        if not found:
            print("No direct relationships found to 'bedroom closet'")
            print("\nLet's check if there's a nested relationship...")
            
            # Check for nested relationships (e.g., keys in jacket, jacket in closet)
            result = session.run("""
                MATCH path = (item:Entity)-[r1:RELATES]->(intermediate:Entity)-[r2:RELATES]->(loc:Entity)
                WHERE loc.name =~ '.*closet.*'
                RETURN item.name AS item, 
                       r1.type AS rel1,
                       intermediate.name AS intermediate,
                       r2.type AS rel2,
                       loc.name AS location
                LIMIT 10
            """)
            
            found_nested = False
            for record in result:
                found_nested = True
                print(f"Nested: {record['item']} --[{record['rel1']}]--> {record['intermediate']} --[{record['rel2']}]--> {record['location']}")
            
            if not found_nested:
                print("No nested relationships found either.")
    
    kg.close()
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

