#!/usr/bin/env python3
"""
Main entry point for the Knowledge Graph Flask application
"""

from app import create_app
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Determine the configuration based on environment
config_name = os.getenv("FLASK_ENV", "development")

app = create_app(config_name)

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 9000)),
        debug=app.config["DEBUG"]
    )
