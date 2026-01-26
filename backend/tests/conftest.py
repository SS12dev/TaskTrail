import sys
from pathlib import Path

# Add the backend directory to the Python path so tests can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
