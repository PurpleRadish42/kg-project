#!/bin/bash
# Quick start script for the Knowledge Graph System

set -e

echo "=================================================="
echo "Knowledge Graph System - Quick Start"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with your configuration:"
    echo ""
    echo "cat > .env << EOF"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    echo "NEO4J_URI=bolt://localhost:7687"
    echo "NEO4J_USER=neo4j"
    echo "NEO4J_PASSWORD=password"
    echo "EOF"
    echo ""
    exit 1
fi

# Check if Neo4j is running
echo "Checking Neo4j connection..."
if ! nc -z localhost 7687 2>/dev/null; then
    echo "❌ Error: Cannot connect to Neo4j on port 7687"
    echo ""
    echo "Please start Neo4j first:"
    echo "  docker-compose up -d"
    echo ""
    echo "Or:"
    echo "  docker run -d --name kg-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest"
    echo ""
    exit 1
fi

echo "✓ Neo4j is running"
echo ""

# Run the script
echo "Running Knowledge Graph System..."
echo ""
python kg_system.py

echo ""
echo "=================================================="
echo "✓ Complete! Check the output above for results."
echo "=================================================="
echo ""
echo "View the graph in Neo4j Browser: http://localhost:7474"
echo "Username: neo4j, Password: password"

