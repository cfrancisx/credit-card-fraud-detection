from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database - use PostgreSQL for Render, fallback to SQLite
try:
    from models.database_render import DatabaseRender as Database
    print("✅ Using PostgreSQL database (Render)")
except ImportError as e:
    print(f"⚠️ PostgreSQL not available: {e}")
    try:
        from models.database import Database
        print("✅ Using MySQL database (local)")
    except ImportError:
        # Fallback to simple in-memory database for demo
        from models.database_simple import DatabaseSimple as Database
        print("✅ Using simple database (fallback)")

# Initialize fraud models
try:
    from models.fraud_models import FraudDetectionModels
    fraud_models = FraudDetectionModels()
except ImportError:
    # Create a simple fallback
    class SimpleFraudModels:
        def predict(self, transaction_data):
            return {
                'rf_score': 0.1,
                'lr_score': 0.1,
                'final_score': 0.1
            }
    fraud_models = SimpleFraudModels()
    print("✅ Using simple fraud models (fallback)")

db = Database()

# Your existing routes below...
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    try:
        metrics = db.get_system_metrics()
        recent_transactions = db.get_recent_transactions(10)
        return render_template('dashboard.html', 
                             metrics=metrics, 
                             transactions=recent_transactions)
    except Exception as e:
        # Fallback data for demo
        return render_template('dashboard.html', 
                             metrics={'total_transactions': 0, 'fraudulent_count': 0, 'detection_rate': 0, 'suspicious_count': 0}, 
                             transactions=[])

# ... include all your other routes ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)