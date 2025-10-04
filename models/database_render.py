"""
PostgreSQL database for Render deployment - Auto-creates database if needed
"""
import os
from datetime import datetime
import json

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️ psycopg2 not available - using fallback")

class DatabaseRender:
    def __init__(self):
        self.connection = None
        if POSTGRES_AVAILABLE:
            self._ensure_database_exists()
            self._ensure_tables_exist()
    
    def _ensure_database_exists(self):
        """Ensure the database exists, create if it doesn't"""
        if not POSTGRES_AVAILABLE:
            return
            
        try:
            # First connect without specifying database to check/create it
            admin_conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'password'),
                port=os.environ.get('DB_PORT', 5432),
                database='postgres'  # Connect to default postgres database
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = admin_conn.cursor()
            
            # Check if our database exists
            db_name = os.environ.get('DB_NAME', 'fraud_detection')
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                print(f"📦 Creating database: {db_name}")
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                print(f"✅ Database '{db_name}' created successfully")
            else:
                print(f"✅ Database '{db_name}' already exists")
            
            cursor.close()
            admin_conn.close()
            
        except Exception as e:
            print(f"⚠️ Database creation check failed: {e}")
    
    def get_connection(self):
        if not POSTGRES_AVAILABLE:
            return None
            
        if not self.connection or (hasattr(self.connection, 'closed') and self.connection.closed):
            try:
                # Get database name from environment or use default
                db_name = os.environ.get('DB_NAME', 'fraud_detection')
                
                self.connection = psycopg2.connect(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    database=db_name,
                    user=os.environ.get('DB_USER', 'postgres'),
                    password=os.environ.get('DB_PASSWORD', 'password'),
                    port=os.environ.get('DB_PORT', 5432),
                    connect_timeout=10
                )
                print(f"✅ Connected to PostgreSQL database: {db_name}")
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                print("💡 Using fallback database instead")
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
            tables_created = []
            
            # Cardholders table
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
            tables_created.append('cardholders')
            
            # Transactions table
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
            tables_created.append('transactions')
            
            # Fraud detection logs table
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
            tables_created.append('fraud_detection_logs')
            
            # Case management table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_management (
                    case_id SERIAL PRIMARY KEY,
                    transaction_id INTEGER,
                    risk_level VARCHAR(10),
                    status VARCHAR(20) DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            tables_created.append('case_management')
            
            # Insert sample data if tables are empty
            cursor.execute("SELECT COUNT(*) FROM cardholders")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO cardholders (name, card_number, account_number) 
                    VALUES 
                    ('John Smith', '4111111111111111', 'ACC001'),
                    ('Sarah Johnson', '4222222222222222', 'ACC002'),
                    ('Demo User', '4555555555555555', 'ACC003')
                """)
                print("✅ Sample cardholders added")
            
            conn.commit()
            cursor.close()
            print(f"✅ PostgreSQL tables verified/created: {', '.join(tables_created)}")
            
        except Exception as e:
            print(f"⚠️ PostgreSQL setup warning: {e}")

    # ... keep the rest of your methods the same as before ...
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
            'total_transactions': 125,
            'fraudulent_count': 3,
            'suspicious_count': 8,
            'detection_rate': 97.5
        }
    
    def get_recent_transactions(self, limit=10):
        if not POSTGRES_AVAILABLE:
            return self._get_fallback_transactions()
            
        try:
            conn = self.get_connection()
            if not conn:
                return self._get_fallback_transactions()
                
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
            return self._get_fallback_transactions()
    
    def _get_fallback_transactions(self):
        """Fallback transactions data"""
        return [
            {
                'transaction_id': 1,
                'cardholder_name': 'John Smith',
                'amount': 150.00,
                'merchant_id': 'online_store',
                'location': 'New York, NY',
                'date_time': datetime.now(),
                'created_at': datetime.now()
            },
            {
                'transaction_id': 2,
                'cardholder_name': 'Sarah Johnson',
                'amount': 45.50,
                'merchant_id': 'grocery',
                'location': 'Los Angeles, CA',
                'date_time': datetime.now(),
                'created_at': datetime.now()
            }
        ]
    
    def create_transaction(self, cardholder_id, amount, merchant_id, location, date_time):
        if not POSTGRES_AVAILABLE:
            return len(self._get_fallback_transactions()) + 1
            
        try:
            conn = self.get_connection()
            if not conn:
                return len(self._get_fallback_transactions()) + 1
                
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
            return len(self._get_fallback_transactions()) + 1
    
    def log_fraud_detection(self, transaction_id, score_rf, score_lr, final_score, decision):
        if not POSTGRES_AVAILABLE:
            print(f"📊 Fraud detection (fallback): TXN {transaction_id}, Score: {final_score}, Decision: {decision}")
            return True
            
        try:
            conn = self.get_connection()
            if not conn:
                print(f"📊 Fraud detection (fallback): TXN {transaction_id}, Score: {final_score}, Decision: {decision}")
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
            print(f"📋 Fraud case created (fallback): TXN {transaction_id}, Risk: {risk_level}")
            return True
            
        try:
            conn = self.get_connection()
            if not conn:
                print(f"📋 Fraud case created (fallback): TXN {transaction_id}, Risk: {risk_level}")
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
                'transaction_id': 1,
                'cardholder_name': 'John Smith',
                'amount': 150.00,
                'merchant_id': 'online',
                'location': 'New York, NY',
                'risk_level': 'Medium',
                'status': 'Pending',
                'created_at': datetime.now()
            },
            {
                'case_id': 2,
                'transaction_id': 2,
                'cardholder_name': 'Sarah Johnson',
                'amount': 45.50,
                'merchant_id': 'grocery',
                'location': 'Los Angeles, CA',
                'risk_level': 'Low',
                'status': 'Resolved',
                'created_at': datetime.now()
            }
        ]