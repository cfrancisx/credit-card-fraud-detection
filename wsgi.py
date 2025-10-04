import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/credit-card-fraud-detection'
if path not in sys.path:
    sys.path.insert(0, path)

# Import your Flask application
from app import app as application

# Optional: Configure any production settings
application.debug = False