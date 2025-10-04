"""
PostgreSQL database for Render deployment
"""
import os
from datetime import datetime
import json

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️ psycopg2 not available - using fallback")

class DatabaseRender:
    def __init__(self):
        self.connection = None
        if POSTGRES_AVAILABLE:
            self._ensure_tables_exist()
    
    def get_connection(self):
        if not POSTGRES_AVAILABLE:
            return None
            
        if not self.connection or (hasattr(self.connection, 'closed') and self.connection.closed):
            try:
                # Use environment variables from Render
                self.connection = psycopg2.connect(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    database=os.environ.get('DB_NAME', 'fraud_detection'),
                    user=os.environ.get('DB_USER', 'postgres'),
                    password=os.environ.get('DB_PASSWORD', 'password'),
                    port=os.environ.get('DB_PORT', 5432),
                    connect_timeout=10
                )
                print("✅ Connected to PostgreSQL database")
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                self.connection = None
        return self.connection
    
    def _ensure_tables_exist(self):
        """Create tables if they don't exist"""
        if not POSTGRES_AVAILABLE:
            return
            
        try:
            conn = self.get_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cardholders (
                    cardholder_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    card_number VARCHAR(16),
                    account_number VARCHAR(20),
                    behavior_profile JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    cardholder_id INTEGER,
                    amount DECIMAL(10,2),
                    merchant_id VARCHAR(20),
                    location VARCHAR(100),
                    date_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_detection_logs (
                    log_id SERIAL PRIMARY KEY,
                    transaction_id INTEGER,
                    score_rf DECIMAL(4,2),
                    score_lr DECIMAL(4,2),
                    final_score DECIMAL(4,2),
                    decision VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_management (
                    case_id SERIAL PRIMARY KEY,
                    transaction_id INTEGER,
                    risk_level VARCHAR(10),
                    status VARCHAR(20) DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert sample data if empty
            cursor.execute("SELECT COUNT(*) FROM cardholders")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO cardholders (name, card_number, account_number) 
                    VALUES 
                    ('John Smith', '4111111111111111', 'ACC001'),
                    ('Sarah Johnson', '4222222222222222', 'ACC002')
                """)
            
            conn.commit()
            cursor.close()
            print("✅ PostgreSQL tables verified/created")
            
        except Exception as e:
            print(f"⚠️ PostgreSQL setup warning: {e}")

    def get_system_metrics(self):
        """Get basic system metrics"""
        if not POSTGRES_AVAILABLE:
            return self._get_fallback_metrics()
            
        try:
            conn = self.get_connection()
            if not conn:
                return self._get_fallback_metrics()
                
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM fraud_detection_logs WHERE decision = 'Fraudulent'")
            fraud = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM case_management")
            suspicious = cursor.fetchone()[0]
            
            detection_rate = (fraud / total * 100) if total > 0 else 0
            
            cursor.close()
            
            return {
                'total_transactions': total,
                'fraudulent_count': fraud,
                'suspicious_count': suspicious,
                'detection_rate': round(detection_rate, 2)
            }
            
        except Exception as e:
            print(f"⚠️ Error getting metrics: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self):
        """Fallback metrics when database is unavailable"""
        return {
            'total_transactions': 0,
            'fraudulent_count': 0,
            'suspicious_count': 0,
            'detection_rate': 0.0
        }
    
    def get_recent_transactions(self, limit=10):
        if not POSTGRES_AVAILABLE:
            return []
            
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, c.name as cardholder_name 
                FROM transactions t 
                LEFT JOIN cardholders c ON t.cardholder_id = c.cardholder_id 
                ORDER BY t.created_at DESC 
                LIMIT %s
            """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            transactions = [dict(zip(columns, row)) for row in results]
            
            cursor.close()
            return transactions
            
        except Exception as e:
            print(f"⚠️ Error getting transactions: {e}")
            return []
    
    def create_transaction(self, cardholder_id, amount, merchant_id, location, date_time):
        if not POSTGRES_AVAILABLE:
            return 1  # Return dummy ID
            
        try:
            conn = self.get_connection()
            if not conn:
                return 1
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (cardholder_id, amount, merchant_id, location, date_time)
                VALUES (%s, %s, %s, %s, %s) RETURNING transaction_id
            """, (cardholder_id, amount, merchant_id, location, date_time))
            
            transaction_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return transaction_id
            
        except Exception as e:
            print(f"⚠️ Error creating transaction: {e}")
            return 1
    
    def log_fraud_detection(self, transaction_id, score_rf, score_lr, final_score, decision):
        if not POSTGRES_AVAILABLE:
            return True
            
        try:
            conn = self.get_connection()
            if not conn:
                return True
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fraud_detection_logs (transaction_id, score_rf, score_lr, final_score, decision)
                VALUES (%s, %s, %s, %s, %s)
            """, (transaction_id, score_rf, score_lr, final_score, decision))
            
            conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"⚠️ Error logging fraud detection: {e}")
            return True
    
    def create_fraud_case(self, transaction_id, risk_level):
        if not POSTGRES_AVAILABLE:
            return True
            
        try:
            conn = self.get_connection()
            if not conn:
                return True
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO case_management (transaction_id, risk_level, status)
                VALUES (%s, %s, 'Pending')
            """, (transaction_id, risk_level))
            
            conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"⚠️ Error creating fraud case: {e}")
            return True
    
    def get_fraud_cases(self):
        if not POSTGRES_AVAILABLE:
            return self._get_fallback_cases()
            
        try:
            conn = self.get_connection()
            if not conn:
                return self._get_fallback_cases()
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cm.*, t.amount, t.merchant_id, t.location, c.name as cardholder_name
                FROM case_management cm
                LEFT JOIN transactions t ON cm.transaction_id = t.transaction_id
                LEFT JOIN cardholders c ON t.cardholder_id = c.cardholder_id
                ORDER BY cm.created_at DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            cases = [dict(zip(columns, row)) for row in results]
            
            cursor.close()
            return cases
            
        except Exception as e:
            print(f"⚠️ Error getting fraud cases: {e}")
            return self._get_fallback_cases()
    
    def _get_fallback_cases(self):
        """Fallback cases when database is unavailable"""
        return [
            {
                'case_id': 1,
                'transaction_id': 'DEMO001',
                'cardholder_name': 'Demo User',
                'amount': 150.00,
                'merchant_id': 'online',
                'location': 'New York, NY',
                'risk_level': 'Medium',
                'status': 'Pending',
                'created_at': datetime.now()
            }
        ]