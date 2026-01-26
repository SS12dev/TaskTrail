#!/usr/bin/env python
"""
Development server launcher for TaskTrail backend.

This script loads environment variables from .env file before starting
the uvicorn server, ensuring all settings are properly initialized.
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Get the backend directory
backend_dir = Path(__file__).parent

# Load environment variables from .env
env_path = backend_dir / '.env'
if env_path.exists():
    print(f"Loading environment from {env_path}")
    load_dotenv(env_path)
else:
    print(f"WARNING: {env_path} not found")

# Start uvicorn server
print("Starting TaskTrail backend server...")
print("Access API at http://127.0.0.1:8000")
print("API docs at http://127.0.0.1:8000/docs\n")

try:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--port",
            "8000",
        ],
        cwd=backend_dir
    )
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
    sys.exit(0)
