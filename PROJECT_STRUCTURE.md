# Project Structure

This document describes the organization of the Knowledge Graph Flask application.

## Directory Layout

```
kg-project/
├── app/                          # Main application package
│   ├── __init__.py              # Flask application factory
│   ├── routes/                  # Route handlers (controllers)
│   │   ├── __init__.py
│   │   ├── api.py               # REST API endpoints (/api/*)
│   │   └── web.py               # Web UI routes (/, /add, /query, etc.)
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── kg_service.py        # Knowledge graph operations
│   │   └── neo4j_service.py     # Neo4j database connection management
│   ├── models/                   # Data models (currently empty, can be extended)
│   │   └── __init__.py
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html            # Base template with navigation
│   │   ├── index.html           # Home page
│   │   ├── add.html             # Add knowledge page
│   │   ├── query.html           # Query page
│   │   └── graph.html           # View graph page
│   └── static/                  # Static assets
│       ├── css/
│       │   └── style.css        # Custom styles
│       └── js/
│           └── main.js          # Custom JavaScript
│
├── legacy/                      # Old scripts (kept for reference)
│   ├── kg_system.py            # Original knowledge graph system
│   └── diagnose_kg.py          # Diagnostic script
│
├── scripts/                     # Utility scripts
│   └── test_legacy.py          # Test script for legacy code
│
├── config.py                    # Application configuration
├── run.py                       # Application entry point
├── docker-compose.yml           # Neo4j Docker setup
├── pyproject.toml               # Python project configuration
├── .env.example                 # Example environment variables
├── .flaskenv                    # Flask environment variables
├── README.md                    # Main documentation
├── PROJECT_STRUCTURE.md         # This file
└── .gitignore                   # Git ignore rules
```

## Architecture Layers

### 1. Route Layer (`app/routes/`)
- **Purpose**: Handle HTTP requests and responses
- **Responsibilities**:
  - Parse request data
  - Call service methods
  - Format responses (JSON for API, HTML for web)
  - Handle errors and flash messages
- **Files**:
  - `api.py`: REST API endpoints returning JSON
  - `web.py`: Web UI routes returning HTML templates

### 2. Service Layer (`app/services/`)
- **Purpose**: Business logic and data operations
- **Responsibilities**:
  - Knowledge extraction from text
  - Knowledge storage in Neo4j
  - Query processing and reasoning
  - Database operations
- **Files**:
  - `kg_service.py`: Knowledge graph operations
  - `neo4j_service.py`: Neo4j connection management

### 3. Template Layer (`app/templates/`)
- **Purpose**: User interface presentation
- **Technology**: Jinja2 templating engine
- **Files**:
  - `base.html`: Base template with navigation and footer
  - `index.html`: Home page with feature overview
  - `add.html`: Form to add knowledge from text
  - `query.html`: Form to query the knowledge graph
  - `graph.html`: View all entities and relationships

### 4. Static Assets (`app/static/`)
- **Purpose**: CSS, JavaScript, and other static files
- **Files**:
  - `css/style.css`: Custom styling
  - `js/main.js`: Client-side JavaScript

## Data Flow

### Adding Knowledge
```
User Input (Text)
    ↓
Web Route (/add) or API Route (/api/add)
    ↓
KnowledgeGraphService.extract_knowledge()
    ↓
GPT-4o-mini API
    ↓
KnowledgeGraphService.store_knowledge()
    ↓
Neo4jService (Neo4j Database)
```

### Querying Knowledge
```
User Question
    ↓
Web Route (/query) or API Route (/api/query)
    ↓
KnowledgeGraphService.query_knowledge()
    ↓
Neo4jService (Query Graph)
    ↓
GPT-4o-mini (Reason over Graph Data)
    ↓
Answer to User
```

## Configuration

- **`config.py`**: Centralized configuration using Flask config pattern
- **`.env`**: Environment-specific variables (not in git)
- **`.flaskenv`**: Flask-specific environment variables

## Key Design Decisions

1. **Service Layer Pattern**: Separates business logic from HTTP handling
2. **Singleton Pattern**: Neo4j service uses singleton for connection management
3. **Blueprint Pattern**: Flask blueprints for modular route organization
4. **Factory Pattern**: Flask app factory in `app/__init__.py`
5. **Template Inheritance**: Base template for consistent UI

## Extending the Application

### Adding a New Route
1. Create route handler in `app/routes/web.py` or `app/routes/api.py`
2. Register blueprint if creating new blueprint
3. Create template if needed in `app/templates/`

### Adding a New Service
1. Create service class in `app/services/`
2. Import and use in routes
3. Add to `app/services/__init__.py` exports

### Adding a New Template
1. Create template in `app/templates/`
2. Extend `base.html` for consistency
3. Add route in `app/routes/web.py`

## Testing Strategy

- Unit tests: Test service methods in isolation
- Integration tests: Test route handlers with services
- E2E tests: Test full user workflows

(Test files to be added in `tests/` directory)


