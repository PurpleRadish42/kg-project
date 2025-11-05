# Usage Example

## What the System Does

This knowledge graph system takes natural language text and:
1. **Extracts** structured information (entities, relationships, properties)
2. **Stores** it in Neo4j with temporal metadata
3. **Answers** questions by querying the knowledge graph

## Example Walkthrough

### Input Text
```
On Monday morning, I placed my car keys on the kitchen counter next to the coffee maker. 
Later that afternoon, my roommate moved them to the key hook by the front door because 
he needed to use the car. The coffee maker is a Breville model that I bought in January 
2024, and it's usually kept plugged in on the left side of the counter. My car is a blue 
Honda Civic parked in the garage, and I typically drive it to work every weekday. The 
front door key hook was installed by my roommate last month specifically for keeping keys 
organized. On Tuesday evening, the keys were missing from the hook, and I found them in 
my roommate's jacket pocket in the bedroom closet.
```

### What Gets Extracted

**Entities:**
- car keys (Object)
- kitchen counter (Location)
- coffee maker (Object)
- key hook (Object)
- front door (Location)
- roommate (Person)
- car (Object - blue Honda Civic)
- garage (Location)
- bedroom closet (Location)
- roommate's jacket (Object)

**Relationships (with temporal tracking):**
- car keys → LOCATED_AT → kitchen counter (Monday morning)
- car keys → MOVED_TO → key hook (Monday afternoon)
- car keys → LOCATED_AT → roommate's jacket pocket (Tuesday evening) [CURRENT]
- coffee maker → LOCATED_AT → kitchen counter
- coffee maker → HAS_PROPERTY → brand: Breville
- car → LOCATED_AT → garage
- car → HAS_PROPERTY → color: blue, model: Honda Civic

### Questions and Expected Answers

**Q: "Where are my car keys?"**
Expected Answer: Based on temporal tracking, the most recent location (Tuesday evening) 
is in the roommate's jacket pocket in the bedroom closet.

**Q: "Where is the coffee maker?"**
Expected Answer: On the kitchen counter, specifically on the left side and kept plugged in.

**Q: "What's in the bedroom closet?"**
Expected Answer: The roommate's jacket (which contains the car keys in the pocket).

**Q: "What items are on the kitchen counter?"**
Expected Answer: The coffee maker (Breville model) and potentially reference to where 
the car keys were initially placed Monday morning.

## How to Customize for Your Own Use

### 1. Process Your Own Text

```python
from kg_system import KnowledgeGraphSystem

kg = KnowledgeGraphSystem()

# Your custom paragraph
my_text = """
Your own contextual information here...
"""

# Extract and store
knowledge = kg.extract_knowledge(my_text)
kg.store_knowledge(knowledge, my_text)

# Ask questions
answer = kg.query_knowledge("Your question here?")
print(answer)

kg.close()
```

### 2. Add New Information Over Time

```python
# Day 1
kg.store_knowledge(
    kg.extract_knowledge("I put my phone in the living room"), 
    "Day 1 context"
)

# Day 2
kg.store_knowledge(
    kg.extract_knowledge("I moved my phone to the bedroom"), 
    "Day 2 context"
)

# Query will return the most recent location
answer = kg.query_knowledge("Where is my phone?")
# Expected: "Your phone is in the bedroom"
```

### 3. Query the Graph Directly

You can also run Cypher queries directly in Neo4j browser (http://localhost:7474):

```cypher
// Find all objects and their current locations
MATCH (obj:Entity)-[r:RELATES {type: 'LOCATED_AT'}]->(loc:Entity)
WHERE obj.type = 'Object'
RETURN obj.name, loc.name, r.timestamp
ORDER BY r.timestamp DESC

// Find everything in a specific location
MATCH (item:Entity)-[r:RELATES {type: 'LOCATED_AT'}]->(loc:Entity {name: 'bedroom closet'})
RETURN item.name, item.type

// Track movement of a specific item
MATCH (item:Entity {name: 'car keys'})-[r:RELATES]-(loc:Entity)
RETURN item.name, r.type, loc.name, r.timestamp
ORDER BY r.timestamp
```

## Integration with Your Research

This prototype demonstrates key concepts from your research abstract:

✅ **Natural Language Input**: Users define facts through natural language  
✅ **Structured Storage**: Information parsed into knowledge graph triples  
✅ **Temporal Metadata**: Tracks when events occurred  
✅ **Provenance Tracking**: Stores source text for each fact  
✅ **Adaptive Reasoning**: Answers queries using most recent information  
✅ **Local Operation**: Runs on local Neo4j instance (privacy-preserving)  
✅ **Context-Aware**: Captures household/local context

## Next Steps for Enhancement

1. **Conflict Resolution**: Add logic to handle contradictory information
2. **Vector Search**: Implement hybrid retrieval with embeddings
3. **Multi-User Context**: Track who provided each piece of information
4. **Continuous Learning**: Auto-update graph from conversations
5. **Explanation System**: Provide reasoning chains for answers
6. **Privacy Audit**: Implement data retention and deletion policies

