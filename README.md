# Knowledge Graph AI - Flask Demo

A Flask application that extracts knowledge from natural language text using GPT-4o-mini, stores it in a Neo4j knowledge graph, and answers questions through intelligent querying.

## Features

- **User Authentication** - Register and login with PostgreSQL
- **Multi-user Support** - Each user has their own knowledge graph context
- **Welcome Page** - Beautiful landing page with demo access
- **Demo Mode** - Try the system without registration (stores as "demo_user")
- **Automatic knowledge extraction** from natural language text
- **Neo4j graph storage** with temporal and relationship tracking
- **User-specific data isolation** - Your data stays separate from others
- **Intelligent question answering** using the knowledge graph
- **REST API** for programmatic access

## Prerequisites

- Python 3.13+
- Neo4j Database (Aura Cloud or local)
- PostgreSQL Database (for user authentication)
- OpenAI API key

## Setup

### 1. Configure Environment

Create a `.env` file:

```bash
OPENAI_MODEL=gpt-4o-mini                              # Model to use (default)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io # Neo4j Aura URI
NEO4J_USERNAME=neo4j                                  # Neo4j username
NEO4J_PASSWORD=your_password                          # Neo4j password
NEO4J_DATABASE=neo4j                                  # Database name (usually 'neo4j')
SECRET_KEY=your-secret-key                            # Flask secret key
EOF
```

**Important:** Replace `your_openai_api_key_here` with your actual OpenAI API key.

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the Application

```bash
uv run python run.py
```

The application will start on http://localhost:5000

## Usage

### Welcome Page

Open http://localhost:5000 in your browser - you'll see a welcome page with options to:
- **Try Demo** - Test the system without registration (data saved as "demo_user")
- **Register** - Create your own account for personalized storage
- **Login** - Access your personal knowledge graph

### Demo Mode

1. Click "Try Demo" on the welcome page
2. Read the test paragraph about car keys, coffee maker, etc.
3. Click **"Store Data in Knowledge Graph"**
4. Wait for the loading animation (3-5 seconds)
5. Click **"Answer"** on any of the 4 test questions
6. See the knowledge graph in action!

**Note:** Demo mode stores data as "demo_user" in Neo4j

### User Accounts

1. **Register** - Create an account with username, email, and password
2. **Login** - Access your personal knowledge graph
3. **Your Data** - All your knowledge graph data is isolated by your username
4. **Try Demo** - You can still access the demo even when logged in

### REST API

#### Store Knowledge
```bash
curl -X POST http://localhost:5000/api/add \
  -H "Content-Type: application/json" \
  -d '{"text": "I placed my keys on the table."}'
```

#### Query Knowledge
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Where are my keys?"}'
```

#### Get All Entities
```bash
curl http://localhost:5000/api/entities
```

#### Get All Relationships
```bash
curl http://localhost:5000/api/relationships
```

## Project Structure

```
kg-project/
├── app/
│   ├── routes/          # API and web routes
│   ├── services/        # Business logic (KG and Neo4j)
│   ├── templates/       # HTML templates
│   └── static/          # CSS and JS
├── config.py            # Configuration
├── run.py               # Application entry point
└── docker-compose.yml   # Neo4j setup
```

## How It Works

1. **Extract**: GPT-4o-mini analyzes text and extracts entities, relationships, and temporal information
2. **Store**: Structured knowledge is stored in Neo4j with timestamps and provenance
3. **Query**: Questions are answered by reasoning over the knowledge graph using GPT-4o-mini

## Troubleshooting

### Neo4j Connection Error
- Verify your Neo4j Aura instance is running
- Check that NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are correct in `.env`
- Ensure your IP is whitelisted in Neo4j Aura (or allow 0.0.0.0/0 for testing)

### OpenAI API Error
- Verify API key is correct in `.env`
- Check you have credits at https://platform.openai.com/usage

### Page Won't Load
- Make sure Flask is running on port 5000
- Check terminal for error messages

## Configuration

Edit `.env` file:

```env
OPENAI_API_KEY=your_api_key                           # Required
OPENAI_MODEL=gpt-4o-mini                              # Model to use (default)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io # Neo4j Aura URI
NEO4J_USERNAME=neo4j                                  # Neo4j username
NEO4J_PASSWORD=your_password                          # Neo4j password
NEO4J_DATABASE=neo4j                                  # Database name (usually 'neo4j')
SECRET_KEY=your-secret-key                            # Flask secret key
```
