-- This SQL script creates the necessary tables for the transaction management system.
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    name VARCHAR(100),
    phone VARCHAR(15),
    date TIMESTAMP NOT NULL,
    fees INTEGER,
    CONSTRAINT valid_type CHECK (type IN (
        'Incoming Money',
        'Payments to Code Holders',
        'Transfers to Mobile Numbers',
        'Withdrawals from Agents',
        'Bank Transfers',
        'Airtime/Data/Bundle Purchases',
        'Utility Payments',
        'Third-party Initiated Transactions'
    ))
);

CREATE INDEX idx_date ON transactions(date);
CREATE INDEX idx_type ON transactions(type);