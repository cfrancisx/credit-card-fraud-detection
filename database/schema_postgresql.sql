-- Cardholders table
CREATE TABLE cardholders (
    cardholder_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    card_number VARCHAR(16) NOT NULL UNIQUE,
    account_number VARCHAR(20) NOT NULL,
    behavior_profile JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    cardholder_id INTEGER NOT NULL REFERENCES cardholders(cardholder_id),
    amount DECIMAL(10,2) NOT NULL,
    merchant_id VARCHAR(20) NOT NULL,
    location VARCHAR(100) NOT NULL,
    date_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fraud detection logs table
CREATE TABLE fraud_detection_logs (
    log_id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(transaction_id),
    score_rf DECIMAL(4,2) NOT NULL,
    score_lr DECIMAL(4,2) NOT NULL,
    final_score DECIMAL(4,2) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Case management table
CREATE TABLE case_management (
    case_id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(transaction_id),
    risk_level VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    audit_trail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO cardholders (name, card_number, account_number, behavior_profile) VALUES
('John Smith', '4111111111111111', 'ACC001', '{"avg_transaction": 85.50, "usual_merchants": ["retail", "grocery"]}'),
('Sarah Johnson', '4222222222222222', 'ACC002', '{"avg_transaction": 120.75, "usual_merchants": ["online", "travel"]}');