import xml.etree.ElementTree as ET
import re
import logging
from datetime import datetime

# Configure logging to file
logging.basicConfig(
    filename='backend/unprocessed_sms.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Valid transaction types from transaction_categories
VALID_TYPES = {
    'INCOMING_MONEY', 'PAYMENT_TO_CODE', 'TRANSFER_MOBILE', 'WITHDRAWAL_AGENT',
    'BANK_TRANSFER', 'AIRTIME_PURCHASE', 'UTILITY_PAYMENT', 'THIRD_PARTY',
    'FEE_CHARGE', 'BALANCE_INQUIRY', 'UNKNOWN'
}

def parse_amount(text):
    """Extract amount in RWF from SMS text."""
    match = re.search(r'(\d+\.?\d*) RWF', text)
    return float(match.group(1)) if match else None

def parse_date(text):
    """Extract date in format YYYY-MM-DD HH:MM:SS."""
    match = re.search(r'Date: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    return None

def parse_transaction_id(text):
    """Extract transaction ID."""
    match = re.search(r'Transaction ID: (\w+)', text)
    return match.group(1) if match else None

def parse_phone_number(text):
    """Extract 10-digit phone number."""
    match = re.search(r'\b\d{10}\b', text)
    return match.group(0) if match else None

def parse_name(text, direction):
    """Extract sender or receiver name based on direction ('from' or 'to')."""
    pattern = r'from (\w+\s+\w+)' if direction == 'from' else r'to (\w+\s+\w+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None

def parse_agent_name(text):
    """Extract agent name."""
    match = re.search(r'agent (\w+\s+\w+)', text, re.IGNORECASE)
    return match.group(1) if match else None

def parse_agent_code(text):
    """Extract agent code."""
    match = re.search(r'Agent Code: (\w+)', text, re.IGNORECASE)
    return match.group(1) if match else None

def parse_balance_after(text):
    """Extract balance after transaction."""
    match = re.search(r'Balance: (\d+\.?\d*) RWF', text, re.IGNORECASE)
    return float(match.group(1)) if match else None

def parse_fees(text):
    """Extract transaction fees."""
    match = re.search(r'Fee: (\d+\.?\d*) RWF', text, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0

def categorize_transaction(text):
    """Categorize transaction based on SMS content."""
    text = text.lower()
    if 'received' in text:
        return 'INCOMING_MONEY'
    elif 'payment to code holder' in text:
        return 'PAYMENT_TO_CODE'
    elif 'sent' in text or ('transferred to' in text and 'mobile' in text):
        return 'TRANSFER_MOBILE'
    elif 'withdrawn from' in text:
        return 'WITHDRAWAL_AGENT'
    elif 'bank transfer' in text:
        return 'BANK_TRANSFER'
    elif 'airtime' in text or 'data' in text or 'bundle' in text:
        return 'AIRTIME_PURCHASE'
    elif 'cash power' in text or 'utility' in text:
        return 'UTILITY_PAYMENT'
    elif 'third party' in text:
        return 'THIRD_PARTY'
    elif 'fee' in text and 'service' in text:
        return 'FEE_CHARGE'
    elif 'balance' in text and 'inquiry' in text:
        return 'BALANCE_INQUIRY'
    return 'UNKNOWN'

def parse_sms(xml_file):
    """
    Parse SMS XML file and return a list of transactions and processing logs.
    Returns: (transactions, logs) where transactions are for the transactions table
    and logs are for the processing_log table.
    """
    transactions = []
    logs = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML file: {e}")
        logs.append({
            'sms_body': None,
            'status': 'FAILED',
            'error_message': f"XML parsing error: {str(e)}"
        })
        return transactions, logs

    for sms in root.findall('sms'):
        body = sms.find('body').text
        if not body:
            logging.warning(f"Empty SMS body: {ET.tostring(sms, encoding='unicode')}")
            logs.append({
                'sms_body': None,
                'status': 'SKIPPED',
                'error_message': 'Empty SMS body'
            })
            continue

        transaction_type = categorize_transaction(body)
        if transaction_type not in VALID_TYPES:
            transaction_type = 'UNKNOWN'

        transaction = {
            'transaction_id': parse_transaction_id(body),
            'transaction_type': transaction_type,
            'amount': parse_amount(body),
            'currency': 'RWF',
            'sender_name': parse_name(body, 'from'),
            'receiver_name': parse_name(body, 'to'),
            'phone_number': parse_phone_number(body),
            'agent_name': parse_agent_name(body),
            'agent_code': parse_agent_code(body),
            'transaction_date': parse_date(body),
            'fees': parse_fees(body),
            'balance_after': parse_balance_after(body),
            'raw_sms_body': body
        }

        # Validate required fields
        if None in [transaction['transaction_type'], transaction['transaction_date'], transaction['raw_sms_body']]:
            logging.warning(f"Unprocessable SMS: {body}")
            logs.append({
                'sms_body': body,
                'status': 'FAILED',
                'error_message': 'Missing required fields (type, date, or body)'
            })
            continue

        # Log successful parsing
        logs.append({
            'sms_body': body,
            'status': 'SUCCESS',
            'error_message': None
        })
        transactions.append(transaction)

    return transactions, logs