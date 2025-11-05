# Complete Setup Guide

## Prerequisites

1. **PostgreSQL Docker Container** (already running)
2. **Neo4j Aura Cloud** (already configured)
3. **Python 3.13+** with uv
4. **OpenAI API Key**

## Step-by-Step Setup

### 1. Configure Environment Variables

Create your `.env` file with PostgreSQL credentials:

```bash
cat > .env << EOF
# OpenAI
OPENAI_API_KEY=your_actual_openai_api_key

# Neo4j Aura Cloud
NEO4J_URI=your_aura_uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# PostgreSQL (provide your actual credentials)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kg_users
POSTGRES_USER=your_postgres_username
POSTGRES_PASSWORD=your_postgres_password

# Flask
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
EOF
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the Application

```bash
uv run python run.py
```

The app will automatically:
- Connect to PostgreSQL and create the `users` table
- Connect to Neo4j Aura
- Start the Flask server on http://localhost:5000

## First Time Usage

### 1. Access Welcome Page

Open http://localhost:5000 - you'll see:
- Welcome message
- "Try Demo" button
- Register/Login options (if not logged in)

### 2. Try Demo (No Registration Required)

- Click "Try Demo"
- Test paragraph is pre-loaded
- Click "Store Data in Knowledge Graph"
- Data is saved with `user_id="demo_user"`
- Click "Answer" on any question
- See intelligent responses!

### 3. Create Your Account

- From welcome page, click "Register"
- Enter username, email, and password
- You're automatically logged in
- Now when you use demo, data is saved to YOUR username

## Data Isolation

### Demo User
- `user_id="demo_user"` in Neo4j
- Shared across all unauthenticated users
- Great for testing

### Registered Users
- `user_id=your_username` in Neo4j
- Completely separate from other users
- Your data is private

## What You Provided

You mentioned you have:
1. ✅ PostgreSQL Docker container running locally
2. ✅ Neo4j Aura cloud database
3. ✅ OpenAI API key

Just provide your PostgreSQL username and password in the `.env` file!

## Testing the Setup

### Test 1: Welcome Page
```bash
curl http://localhost:5000
# Should return HTML with welcome page
```

### Test 2: Register
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&email=test@example.com&password=test123&confirm_password=test123"
```

### Test 3: Demo API
```bash
curl -X POST http://localhost:5000/api/add \
  -H "Content-Type: application/json" \
  -d '{"text": "My keys are on the table."}'
# Data stored as demo_user
```

## Troubleshooting

### PostgreSQL Connection Error

```bash
# Test PostgreSQL connection
docker ps | grep postgres
# Should show running container

# Test connection
PGPASSWORD=your_password psql -h localhost -U your_username -d kg_users
```

If database doesn't exist:
```bash
# Create it
PGPASSWORD=your_password psql -h localhost -U your_username -c "CREATE DATABASE kg_users;"
```

### Neo4j Connection Error
- Verify credentials in `.env`
- Check Neo4j Aura dashboard
- Ensure IP is whitelisted

### OpenAI API Error
- Verify API key is correct
- Check usage limits

## Database Schema

### PostgreSQL - Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Created automatically on first run!

### Neo4j - Knowledge Graph
```cypher
// Entities with user_id
(:Entity {name: "car keys", user_id: "alice"})

// Relationships with user_id
()-[:RELATES {type: "LOCATED_AT", user_id: "alice"}]->()
```

## URLs

- **Welcome**: http://localhost:5000
- **Demo**: http://localhost:5000/demo
- **Login**: http://localhost:5000/auth/login
- **Register**: http://localhost:5000/auth/register
- **API**: http://localhost:5000/api/*

## Next Steps

1. Update `.env` with your PostgreSQL credentials
2. Run `uv run python run.py`
3. Open http://localhost:5000
4. Try the demo!
5. Register an account
6. Test with your own data

That's it! 🚀

