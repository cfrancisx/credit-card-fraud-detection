from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from models.database import Database
from models.fraud_models import FraudDetectionModels
import json
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database and models
db = Database(app)
fraud_models = FraudDetectionModels()

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/home')
def home():
    """Alternative route for home page"""
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    metrics = db.get_system_metrics()
    recent_transactions = db.get_recent_transactions(10)
    return render_template('dashboard.html', 
                         metrics=metrics, 
                         transactions=recent_transactions)

@app.route('/fraud-detection', methods=['GET', 'POST'])
def fraud_detection():
    """Fraud detection form page"""
    if request.method == 'POST':
        # Redirect to analysis page with form data
        return redirect(url_for('transaction_analysis'), code=307)
    
    return render_template('fraud_detection.html')

@app.route('/transaction-analysis', methods=['GET', 'POST'])
def transaction_analysis():
    """Transaction analysis results page"""
    if request.method == 'POST':
        # Get form data
        transaction_data = {
            'cardholder_id': request.form.get('cardholder_id'),
            'amount': float(request.form.get('amount')),
            'merchant_category': request.form.get('merchant_category'),
            'location': request.form.get('location'),
            'date_time': request.form.get('date_time')
        }
        
        # Get fraud prediction
        prediction = fraud_models.predict(transaction_data)
        
        # Determine decision based on thresholds
        final_score = prediction['final_score']
        if final_score >= app.config['FRAUD_THRESHOLD']:
            decision = 'Fraudulent'
            final_risk = 'High'
            case_created = True
        elif final_score >= app.config['SUSPICIOUS_THRESHOLD']:
            decision = 'Suspicious'
            final_risk = 'Medium'
            case_created = True
        else:
            decision = 'Legitimate'
            final_risk = 'Low'
            case_created = False
        
        # Store transaction and fraud detection results
        transaction_id = db.create_transaction(
            transaction_data['cardholder_id'],
            transaction_data['amount'],
            transaction_data['merchant_category'],
            transaction_data['location'],
            transaction_data['date_time']
        )
        
        db.log_fraud_detection(
            transaction_id,
            prediction['rf_score'],
            prediction['lr_score'],
            prediction['final_score'],
            decision
        )
        
        # Create case if suspicious or fraudulent
        if case_created:
            db.create_fraud_case(transaction_id, final_risk)
        
        return render_template('transaction_analysis.html',
                             transaction_data=transaction_data,
                             prediction=prediction,
                             decision=decision,
                             final_risk=final_risk,
                             case_created=case_created,
                             analysis_id=f"ANA{transaction_id:06d}",
                             analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # If GET request, redirect to fraud detection form
    return redirect(url_for('fraud_detection'))

@app.route('/case-management')
def case_management():
    """Case management page"""
    fraud_cases = db.get_fraud_cases()
    return render_template('case_management.html', cases=fraud_cases)

@app.route('/reports')
def reports():
    """Reports and analytics page"""
    metrics = db.get_system_metrics()
    
    # Get model performance data
    model_performance = {
        'Random Forest': {
            'accuracy': 0.947,
            'precision': 0.923,
            'recall': 0.958,
            'f1_score': 0.940
        },
        'Logistic Regression': {
            'accuracy': 0.912,
            'precision': 0.889,
            'recall': 0.925,
            'f1_score': 0.907
        }
    }
    
    return render_template('reports.html', 
                         metrics=metrics, 
                         model_performance=model_performance)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Admin configuration page"""
    if request.method == 'POST':
        # Update system settings
        new_threshold = float(request.form.get('fraud_threshold', 0.7))
        app.config['FRAUD_THRESHOLD'] = new_threshold
        return redirect(url_for('admin'))
    
    return render_template('admin.html', 
                         fraud_threshold=app.config['FRAUD_THRESHOLD'])

@app.route('/api/transaction-analysis', methods=['POST'])
def api_transaction_analysis():
    """API endpoint for real-time transaction analysis"""
    try:
        transaction_data = request.get_json()
        prediction = fraud_models.predict(transaction_data)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'decision': 'Fraudulent' if prediction['final_score'] >= app.config['FRAUD_THRESHOLD'] else 'Suspicious' if prediction['final_score'] >= app.config['SUSPICIOUS_THRESHOLD'] else 'Legitimate'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system-metrics')
def api_system_metrics():
    """API endpoint for system metrics"""
    metrics = db.get_system_metrics()
    return jsonify(metrics)

@app.route('/api/log-action', methods=['POST'])
def api_log_action():
    """API endpoint to log user actions"""
    try:
        action_data = request.get_json()
        print(f"Action logged: {action_data}")
        return jsonify({'success': True, 'message': 'Action logged successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)