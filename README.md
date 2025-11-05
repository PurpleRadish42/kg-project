# Knowledge Graph-Driven Local AI System

A context-aware AI system that extracts information from natural language text and stores it in a Neo4j knowledge graph for intelligent querying and reasoning.

## Project Abstract

Personalized AI systems often rely heavily on cloud-based services and generalized datasets, which limit their ability to adapt to highly specific local contexts while raising concerns around privacy. This research proposes a knowledge graph-driven local AI model designed to capture and utilize contextual information in dynamic environments such as households. The system allows users to define contextual facts through natural language, which are parsed into structured knowledge graph triples. These facts are stored with temporal and provenance metadata, enabling adaptive reasoning and conflict resolution.

## Features

- **Natural Language Processing**: Extracts entities, relationships, and temporal information from text using GPT-4o-mini
- **Knowledge Graph Storage**: Stores structured information in Neo4j with temporal and provenance metadata
- **Intelligent Querying**: Answers questions by reasoning over the knowledge graph
- **Temporal Awareness**: Tracks changes over time and provides current state information
- **Privacy-Preserving**: Runs locally with your own Neo4j instance

## Prerequisites

- Python 3.13+
- Neo4j database (Docker or local installation)
- OpenAI API key

## Setup

### 1. Start Neo4j Database

Using Docker:
```bash
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=your_actual_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## Usage

Run the test script:
```bash
python kg_system.py
```

This will:
1. Process a test paragraph about car keys, coffee maker, etc.
2. Extract entities and relationships
3. Store them in Neo4j
4. Answer predefined questions about the content

## How It Works

### 1. Knowledge Extraction

The system uses GPT-4o-mini to analyze natural language text and extract:
- **Entities**: Objects, people, locations (e.g., "car keys", "coffee maker", "kitchen counter")
- **Relationships**: Connections between entities (e.g., "car keys LOCATED_AT bedroom closet")
- **Properties**: Attributes of entities (e.g., "coffee maker" has brand "Breville")
- **Temporal Data**: When events occurred (e.g., "Monday morning", "Tuesday evening")

### 2. Knowledge Storage

Information is stored in Neo4j as a graph:
- Nodes represent entities
- Edges represent relationships
- Both include temporal metadata and provenance information

### 3. Query Processing

When you ask a question:
1. The system retrieves relevant information from Neo4j
2. GPT-4o-mini reasons over the graph data
3. Returns the most current, accurate answer based on timestamps

## Example

**Input Text:**
> "On Monday morning, I placed my car keys on the kitchen counter next to the coffee maker. Later that afternoon, my roommate moved them to the key hook by the front door. On Tuesday evening, I found them in my roommate's jacket pocket in the bedroom closet."

**Question:** "Where are my car keys?"

**Answer:** "Your car keys are in your roommate's jacket pocket in the bedroom closet (as of Tuesday evening, the most recent location)."

## Architecture

```
User Input (Natural Language)
         ↓
    GPT-4o-mini (Extraction)
         ↓
    Structured Knowledge
         ↓
    Neo4j Graph Database
         ↓
    Query Processing (GPT-4o-mini + Graph Queries)
         ↓
    Natural Language Answer
```

## Future Enhancements

- Vector-based semantic search for hybrid retrieval
- Conflict resolution for contradictory information
- Multi-user context support
- Real-time updates through continuous monitoring
- Privacy-preserving local model integration

## License

MIT

