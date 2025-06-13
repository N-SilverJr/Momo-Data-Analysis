import sqlite3
import os
from sms_parser import parse_sms

def init_db(db_file):
    """Initialize the database with the schema."""
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign keys
    schema_path = os.path.join(os.path.dirname(__file__), 'db_schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def insert_transactions(db_file, xml_file):
    """Parse XML and insert transactions and logs into the database."""
    # Initialize database if it doesn't exist
    init_db(db_file)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Parse SMS and get transactions and logs
    transactions, logs = parse_sms(xml_file)

    # Insert transactions
    for t in transactions:
        cursor.execute('''
            INSERT OR IGNORE INTO transactions (
                transaction_id, transaction_type, amount, currency,
                sender_name, receiver_name, phone_number,
                agent_name, agent_code, transaction_date,
                fees, balance_after, raw_sms_body
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            t['transaction_id'],
            t['transaction_type'],
            t['amount'],
            t['currency'],
            t['sender_name'],
            t['receiver_name'],
            t['phone_number'],
            t['agent_name'],
            t['agent_code'],
            t['transaction_date'],
            t['fees'],
            t['balance_after'],
            t['raw_sms_body']
        ))

    # Insert processing logs
    for log in logs:
        cursor.execute('''
            INSERT INTO processing_log (sms_body, status, error_message)
            VALUES (?, ?, ?)
        ''', (
            log['sms_body'],
            log['status'],
            log['error_message']
        ))

    conn.commit()
    conn.close()