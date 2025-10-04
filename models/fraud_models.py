import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
from datetime import datetime

class FraudDetectionModels:
    def __init__(self):
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def preprocess_features(self, transaction_data):
        """Preprocess transaction data for model prediction"""
        features = []
        
        # Amount-based features
        features.append(transaction_data['amount'])
        features.append(np.log1p(transaction_data['amount']))  # Log transform
        
        # Time-based features
        transaction_time = datetime.fromisoformat(transaction_data['date_time'])
        features.append(transaction_time.hour)
        features.append(transaction_time.weekday())
        
        # Merchant category encoding (simplified)
        merchant_categories = {
            'retail': 0, 'online': 1, 'travel': 2, 'entertainment': 3,
            'grocery': 4, 'gas': 5, 'other': 6
        }
        features.append(merchant_categories.get(transaction_data.get('merchant_category', 'other'), 6))
        
        # Location-based features (simplified - in real system, use geolocation)
        features.append(1 if 'foreign' in transaction_data.get('location', '').lower() else 0)
        
        # Behavioral features (would normally come from user history)
        features.extend([0, 0, 0])  # Placeholder for actual behavioral features
        
        return np.array(features).reshape(1, -1)
    
    def train_models(self, X_train, y_train):
        """Train both Random Forest and Logistic Regression models"""
        # Scale features for Logistic Regression
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Train Random Forest
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.rf_model.fit(X_train, y_train)
        
        # Train Logistic Regression
        self.lr_model = LogisticRegression(
            random_state=42,
            class_weight='balanced',
            max_iter=1000
        )
        self.lr_model.fit(X_scaled, y_train)
        
        self.is_trained = True
        
        return self
    
    def predict(self, transaction_data):
        """Predict fraud probability using both models"""
        if not self.is_trained:
            # Load pre-trained models or use default behavior
            return self._predict_without_training(transaction_data)
        
        features = self.preprocess_features(transaction_data)
        
        # Random Forest prediction
        rf_prob = self.rf_model.predict_proba(features)[0][1]
        
        # Logistic Regression prediction
        features_scaled = self.scaler.transform(features)
        lr_prob = self.lr_model.predict_proba(features_scaled)[0][1]
        
        return {
            'rf_score': float(rf_prob),
            'lr_score': float(lr_prob),
            'final_score': float((rf_prob + lr_prob) / 2)
        }
    
    def _predict_without_training(self, transaction_data):
        """Fallback prediction when models aren't trained"""
        # Simplified rule-based approach as fallback
        amount = transaction_data['amount']
        merchant = transaction_data.get('merchant_category', 'other')
        
        base_score = 0.1
        
        # Amount-based rules
        if amount > 1000:
            base_score += 0.4
        elif amount > 500:
            base_score += 0.2
        elif amount > 100:
            base_score += 0.1
        
        # Merchant-based rules
        if merchant == 'online':
            base_score += 0.2
        
        # Add some randomness to simulate model behavior
        rf_score = min(0.95, base_score + np.random.normal(0, 0.1))
        lr_score = min(0.95, base_score + np.random.normal(0, 0.08))
        
        return {
            'rf_score': max(0, rf_score),
            'lr_score': max(0, lr_score),
            'final_score': max(0, (rf_score + lr_score) / 2)
        }
    
    def evaluate_models(self, X_test, y_test):
        """Evaluate model performance"""
        if not self.is_trained:
            return None
        
        X_scaled = self.scaler.transform(X_test)
        
        rf_pred = self.rf_model.predict(X_test)
        lr_pred = self.lr_model.predict(X_scaled)
        
        metrics = {}
        
        for model_name, predictions in [('Random Forest', rf_pred), ('Logistic Regression', lr_pred)]:
            metrics[model_name] = {
                'accuracy': accuracy_score(y_test, predictions),
                'precision': precision_score(y_test, predictions),
                'recall': recall_score(y_test, predictions),
                'f1_score': f1_score(y_test, predictions)
            }
        
        return metrics
    
    def save_models(self, filepath):
        """Save trained models to disk"""
        if self.is_trained:
            joblib.dump({
                'rf_model': self.rf_model,
                'lr_model': self.lr_model,
                'scaler': self.scaler
            }, filepath)
    
    def load_models(self, filepath):
        """Load trained models from disk"""
        try:
            models = joblib.load(filepath)
            self.rf_model = models['rf_model']
            self.lr_model = models['lr_model']
            self.scaler = models['scaler']
            self.is_trained = True
        except:
            self.is_trained = False