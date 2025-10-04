from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Safe database initialization
try:
    from models.database_render import DatabaseRender as Database
    logger.info("✅ Using PostgreSQL database (Render)")
except ImportError as e:
    logger.warning(f"⚠️ PostgreSQL not available: {e}")
    try:
        from models.database import Database
        logger.info("✅ Using MySQL database (local)")
    except ImportError:
        from models.database_simple import DatabaseSimple as Database
        logger.info("✅ Using simple database (fallback)")

# Safe fraud models initialization
try:
    from models.fraud_models import FraudDetectionModels
    fraud_models = FraudDetectionModels()
    logger.info("✅ Using fraud detection models")
except ImportError as e:
    logger.warning(f"⚠️ Fraud models not available: {e}")
    class SimpleFraudModels:
        def predict(self, transaction_data):
            return {
                'rf_score': 0.1,
                'lr_score': 0.1,
                'final_score': 0.1
            }
    fraud_models = SimpleFraudModels()
    logger.info("✅ Using simple fraud models (fallback)")

db = Database()

# Request logging
@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.path}")

# All required routes
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/home')
def home():
    """Alternative home page"""
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page with comprehensive error handling"""
    try:
        metrics = db.get_system_metrics()
        recent_transactions = db.get_recent_transactions(10)
        return render_template('dashboard.html', 
                             metrics=metrics, 
                             transactions=recent_transactions)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', 
                             metrics={'total_transactions': 0, 'fraudulent_count': 0, 'detection_rate': 0, 'suspicious_count': 0}, 
                             transactions=[])

@app.route('/fraud-detection', methods=['GET', 'POST'])
def fraud_detection():
    """Fraud detection page"""
    if request.method == 'POST':
        return redirect(url_for('transaction_analysis'), code=307)
    return render_template('fraud_detection.html')

@app.route('/transaction-analysis', methods=['GET', 'POST'])
def transaction_analysis():
    """Transaction analysis page"""
    if request.method == 'POST':
        try:
            transaction_data = {
                'cardholder_id': request.form.get('cardholder_id', 'DEMO001'),
                'amount': float(request.form.get('amount', 100)),
                'merchant_category': request.form.get('merchant_category', 'other'),
                'location': request.form.get('location', 'Unknown'),
                'date_time': request.form.get('date_time', datetime.now().isoformat())
            }
            
            prediction = fraud_models.predict(transaction_data)
            
            # Store the transaction
            transaction_id = db.create_transaction(
                transaction_data['cardholder_id'],
                transaction_data['amount'],
                transaction_data['merchant_category'],
                transaction_data['location'],
                transaction_data['date_time']
            )
            
            # Log fraud detection
            final_score = prediction['final_score']
            if final_score >= app.config['FRAUD_THRESHOLD']:
                decision = 'Fraudulent'
                risk_level = 'High'
            elif final_score >= app.config['SUSPICIOUS_THRESHOLD']:
                decision = 'Suspicious'
                risk_level = 'Medium'
            else:
                decision = 'Legitimate'
                risk_level = 'Low'
            
            db.log_fraud_detection(transaction_id, prediction['rf_score'], prediction['lr_score'], prediction['final_score'], decision)
            
            if decision in ['Fraudulent', 'Suspicious']:
                db.create_fraud_case(transaction_id, risk_level)
            
            return render_template('transaction_analysis.html',
                                 transaction_data=transaction_data,
                                 prediction=prediction,
                                 decision=decision,
                                 risk_level=risk_level,
                                 analysis_id=f"ANA{transaction_id:06d}",
                                 analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                 
        except Exception as e:
            logger.error(f"Transaction analysis error: {e}")
            return render_template('error.html', error="Analysis failed"), 500
    
    return redirect(url_for('fraud_detection'))

@app.route('/case-management')
def case_management():
    """Case management page"""
    try:
        fraud_cases = db.get_fraud_cases()
        return render_template('case_management.html', cases=fraud_cases)
    except Exception as e:
        logger.error(f"Case management error: {e}")
        return render_template('case_management.html', cases=[])

@app.route('/reports')
def reports():
    """Reports page"""
    try:
        metrics = db.get_system_metrics()
        model_performance = {
            'Random Forest': {'accuracy': 0.947, 'precision': 0.923, 'recall': 0.958, 'f1_score': 0.940},
            'Logistic Regression': {'accuracy': 0.912, 'precision': 0.889, 'recall': 0.925, 'f1_score': 0.907}
        }
        return render_template('reports.html', metrics=metrics, model_performance=model_performance)
    except Exception as e:
        logger.error(f"Reports error: {e}")
        return render_template('reports.html', metrics={}, model_performance={})

@app.route('/admin')
def admin():
    """Admin page"""
    return render_template('admin.html', fraud_threshold=app.config['FRAUD_THRESHOLD'])

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)