"""
Simple in-memory database for demo purposes
Used when PostgreSQL/MySQL are not available
"""
from datetime import datetime
import json

class DatabaseSimple:
    def __init__(self):
        self.transactions = []
        self.cases = []
        print("✅ Initialized simple in-memory database")
    
    def get_system_metrics(self):
        return {
            'total_transactions': len(self.transactions),
            'fraudulent_count': 0,
            'suspicious_count': 0,
            'detection_rate': 0.0
        }
    
    def get_recent_transactions(self, limit=10):
        return self.transactions[-limit:] if self.transactions else []
    
    def create_transaction(self, cardholder_id, amount, merchant_id, location, date_time):
        transaction_id = len(self.transactions) + 1
        transaction = {
            'transaction_id': transaction_id,
            'cardholder_id': cardholder_id,
            'amount': amount,
            'merchant_id': merchant_id,
            'location': location,
            'date_time': date_time,
            'created_at': datetime.now()
        }
        self.transactions.append(transaction)
        return transaction_id
    
    def log_fraud_detection(self, transaction_id, score_rf, score_lr, final_score, decision):
        print(f"📊 Fraud detection logged: TXN {transaction_id}, Score: {final_score}, Decision: {decision}")
        return True
    
    def create_fraud_case(self, transaction_id, risk_level):
        case = {
            'case_id': len(self.cases) + 1,
            'transaction_id': transaction_id,
            'risk_level': risk_level,
            'status': 'Pending',
            'created_at': datetime.now()
        }
        self.cases.append(case)
        return True
    
    def get_fraud_cases(self):
        # Add some sample data for demo
        if not self.cases:
            return [
                {
                    'case_id': 1,
                    'transaction_id': 'TXN001',
                    'cardholder_name': 'Demo User',
                    'amount': 150.00,
                    'merchant_id': 'online',
                    'location': 'New York, NY',
                    'risk_level': 'Medium',
                    'status': 'Pending',
                    'created_at': datetime.now()
                }
            ]
        return self.cases
    
    def execute_query(self, query, params=None, fetch=False):
        # Simple implementation for compatibility
        return True