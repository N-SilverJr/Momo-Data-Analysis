     CREATE TABLE transactions (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         transaction_id VARCHAR(50) UNIQUE,
         transaction_type VARCHAR(50) NOT NULL,
         amount DECIMAL(15,2),
         currency VARCHAR(3) DEFAULT 'RWF',
         sender_name VARCHAR(100),
         receiver_name VARCHAR(100),
         phone_number VARCHAR(20),
         agent_name VARCHAR(100),
         agent_code VARCHAR(20),
         transaction_date DATETIME,
         fees DECIMAL(10,2) DEFAULT 0,
         balance_after DECIMAL(15,2),
         raw_sms_body TEXT NOT NULL,
         created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
         updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
     );

     -- Transaction categories lookup table
     CREATE TABLE transaction_categories (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         category_name VARCHAR(50) UNIQUE NOT NULL,
         description TEXT,
         created_at DATETIME DEFAULT CURRENT_TIMESTAMP
     );

     -- Insert default categories
     INSERT INTO transaction_categories (category_name, description) VALUES
     ('INCOMING_MONEY', 'Money received from other users'),
     ('PAYMENT_TO_CODE', 'Payments made to code holders'),
     ('TRANSFER_MOBILE', 'Transfers to mobile numbers'),
     ('WITHDRAWAL_AGENT', 'Cash withdrawals from agents'),
     ('BANK_TRANSFER', 'Transfers to/from bank accounts'),
     ('AIRTIME_PURCHASE', 'Airtime, data, and bundle purchases'),
     ('UTILITY_PAYMENT', 'Utility payments (electricity, water, etc.)'),
     ('THIRD_PARTY', 'Third-party initiated transactions'),
     ('FEE_CHARGE', 'Service fees and charges'),
     ('BALANCE_INQUIRY', 'Balance check messages'),
     ('UNKNOWN', 'Unrecognized transaction types');

     -- SMS processing log table
     CREATE TABLE processing_log (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         sms_body TEXT,
         status VARCHAR(20),
         error_message TEXT,
         processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
     );

     -- Indexes for better query performance
     CREATE INDEX idx_transactions_type ON transactions(transaction_type);
     CREATE INDEX idx_transactions_date ON transactions(transaction_date);
     CREATE INDEX idx_transactions_amount ON transactions(amount);
     CREATE INDEX idx_transactions_phone ON transactions(phone_number);
     CREATE INDEX idx_transactions_tid ON transactions(transaction_id);

     -- View for transaction summaries
     CREATE VIEW transaction_summary AS
     SELECT 
         transaction_type,
         COUNT(*) as transaction_count,
         SUM(amount) as total_amount,
         AVG(amount) as average_amount,
         MIN(amount) as min_amount,
         MAX(amount) as max_amount,
         SUM(fees) as total_fees
     FROM transactions 
     WHERE amount IS NOT NULL
     GROUP BY transaction_type;

     -- View for monthly summaries
     CREATE VIEW monthly_summary AS
     SELECT 
         strftime('%Y-%m', transaction_date) as month,
         transaction_type,
         COUNT(*) as count,
         SUM(amount) as total_amount,
         SUM(fees) as total_fees
     FROM transactions 
     WHERE transaction_date IS NOT NULL
     GROUP BY strftime('%Y-%m', transaction_date), transaction_type
     ORDER BY month DESC;
