# Quick Setup Guide

## Step 1: Start Neo4j Database

Using Docker Compose (recommended):
```bash
docker-compose up -d
```

Or using Docker directly:
```bash
docker run -d \
    --name kg-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

Check if Neo4j is running:
- Web interface: http://localhost:7474
- Login with username: `neo4j`, password: `password`

## Step 2: Install Dependencies

```bash
uv sync
```

## Step 3: Set Up Environment Variables

Create a `.env` file:
```bash
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
EOF
```

**Important:** Replace `your_openai_api_key_here` with your actual OpenAI API key.

## Step 4: Run the Test

```bash
python kg_system.py
```

You should see:
1. Text being processed
2. Entities and relationships extracted
3. Knowledge stored in Neo4j
4. Questions answered based on the knowledge graph

## Verify in Neo4j Browser

1. Open http://localhost:7474
2. Run this query to see all nodes and relationships:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50
```

## Troubleshooting

### Neo4j Connection Error
- Make sure Docker container is running: `docker ps | grep neo4j`
- Check logs: `docker logs kg-neo4j`

### OpenAI API Error
- Verify your API key is correct in `.env`
- Check you have credits: https://platform.openai.com/usage

### Module Not Found
- Run `uv sync` to install dependencies
- Make sure you're using Python 3.13+

