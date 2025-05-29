#!/usr/bin/env python3
"""
Main application entry point for the Lean Hatch API server.
This file imports and runs the Flask application defined in api/api.py.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Flask app from the api module
from api import app, FLASK_HOST, FLASK_PORT

if __name__ == '__main__':
    print(f"Starting Lean Hatch API server on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)