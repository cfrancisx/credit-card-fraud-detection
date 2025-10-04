import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # Render MySQL configurations (we'll use environment variables)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'fraud_detection_system')
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Model paths
    MODEL_PATH = 'models/saved_models/'
    
    # System settings
    FRAUD_THRESHOLD = 0.7
    SUSPICIOUS_THRESHOLD = 0.3