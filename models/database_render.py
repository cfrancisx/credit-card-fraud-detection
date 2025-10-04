import psycopg2
import os
from datetime import datetime
import json

class DatabaseRender:
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        if not self.connection:
            self.connection = psycopg2.connect(
                host=os.environ.get('DB_HOST'),
                database=os.environ.get('DB_NAME'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                port=os.environ.get('DB_PORT', 5432)
            )
        return self.connection
    
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
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results]
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
    
    # Add your existing database methods here, adapted for PostgreSQL
    def get_recent_transactions(self, limit=10):
        query = """
        SELECT t.*, c.name as cardholder_name 
        FROM transactions t 
        JOIN cardholders c ON t.cardholder_id = c.cardholder_id 
        ORDER BY t.date_time DESC 
        LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True)
    
    def get_system_metrics(self):
        # Simplified for demo - implement your actual metrics
        return {
            'total_transactions': 100,
            'fraudulent_count': 5,
            'suspicious_count': 8,
            'detection_rate': 95.0
        }
    
    # Add other methods from your database.py...