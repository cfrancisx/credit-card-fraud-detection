from flask_mysqldb import MySQL
import MySQLdb
import json
from datetime import datetime

class Database:
    def __init__(self, app):
        self.mysql = MySQL(app)
    
    def get_connection(self):
        return self.mysql.connection
    
    def execute_query(self, query, params=None, fetch=False):
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return result
                else:
                    return cursor.lastrowid
            else:
                connection.commit()
                return cursor.lastrowid
                
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # Cardholder operations
    def get_cardholder(self, cardholder_id):
        query = "SELECT * FROM cardholders WHERE cardholder_id = %s"
        return self.execute_query(query, (cardholder_id,), fetch=True)
    
    def create_cardholder(self, name, card_number, account_number, behavior_profile=None):
        query = """
        INSERT INTO cardholders (name, card_number, account_number, behavior_profile, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (name, card_number, account_number, 
                                        json.dumps(behavior_profile) if behavior_profile else None, 
                                        datetime.now()))
    
    # Transaction operations
    def create_transaction(self, cardholder_id, amount, merchant_id, location, date_time):
        query = """
        INSERT INTO transactions (cardholder_id, amount, merchant_id, location, date_time, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (cardholder_id, amount, merchant_id, location, date_time, datetime.now()))
    
    def get_recent_transactions(self, limit=10):
        query = """
        SELECT t.*, c.name as cardholder_name 
        FROM transactions t 
        JOIN cardholders c ON t.cardholder_id = c.cardholder_id 
        ORDER BY t.date_time DESC 
        LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True)
    
    # Fraud detection operations
    def log_fraud_detection(self, transaction_id, score_rf, score_lr, final_score, decision):
        query = """
        INSERT INTO fraud_detection_logs (transaction_id, score_rf, score_lr, final_score, decision, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (transaction_id, score_rf, score_lr, final_score, decision, datetime.now()))
    
    def create_fraud_case(self, transaction_id, risk_level, status='Pending'):
        query = """
        INSERT INTO case_management (transaction_id, risk_level, status, created_at)
        VALUES (%s, %s, %s, %s)
        """
        return self.execute_query(query, (transaction_id, risk_level, status, datetime.now()))
    
    def get_fraud_cases(self):
        query = """
        SELECT cm.*, t.amount, t.merchant_category, t.location, c.name as cardholder_name
        FROM case_management cm
        JOIN transactions t ON cm.transaction_id = t.id
        JOIN cardholders c ON t.cardholder_id = c.cardholder_id
        ORDER BY cm.created_at DESC
        """
        return self.execute_query(query, fetch=True)
    
    # System metrics
    def get_system_metrics(self):
        query_total = "SELECT COUNT(*) as count FROM transactions"
        query_fraud = "SELECT COUNT(*) as count FROM fraud_detection_logs WHERE decision = 'Fraudulent'"
        query_suspicious = "SELECT COUNT(*) as count FROM fraud_detection_logs WHERE decision = 'Suspicious'"
        
        total = self.execute_query(query_total, fetch=True)[0]['count']
        fraud = self.execute_query(query_fraud, fetch=True)[0]['count']
        suspicious = self.execute_query(query_suspicious, fetch=True)[0]['count']
        
        detection_rate = (fraud / total * 100) if total > 0 else 0
        
        return {
            'total_transactions': total,
            'fraudulent_count': fraud,
            'suspicious_count': suspicious,
            'detection_rate': round(detection_rate, 2)
        }