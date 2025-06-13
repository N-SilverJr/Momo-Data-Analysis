import xml.etree.ElementTree as ET
import re
import logging
from datetime import datetime
import csv
import uuid

logging.basicConfig(filename='unprocessed_sms.log', level=logging.WARNING, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def parse_amount(text):
    match = re.search(r'(\d+\.?\d*) RWF', text)
    return int(float(match.group(1))) if match else None

def parse_date(text):
    match = re.search(r'Date: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
    return None

def parse_transaction_id(text):
    match = re.search(r'Transaction ID: (\w+)', text)
    return match.group(1) if match else None

def parse_phone_number(text):
    match = re.search(r'\b\d{10}\b', text)
    return match.group(0) if match else None

def parse_name(text):
    match = re.search(r'from (\w+\s+\w+)', text) or re.search(r'to (\w+\s+\w+)', text)
    return match.group(1) if match else None

def categorize_transaction(text):
    text = text.lower()
    if 'received' in text:
        return 'Incoming Money'
    elif 'payment to code holder' in text:
        return 'Payments to Code Holders'
    elif 'transferred to' in text and 'mobile' in text:
        return 'Transfers to Mobile Numbers'
    elif 'withdrawn from' in text:
        return 'Withdrawals from Agents'
    elif 'bank transfer' in text:
        return 'Bank Transfers'
    elif 'airtime' in text or 'data' in text or 'bundle' in text:
        return 'Airtime/Data/Bundle Purchases'
    elif 'cash power' in text or 'utility' in text:
        return 'Utility Payments'
    elif 'third party' in text:
        return 'Third-party Initiated Transactions'
    return None

def parse_sms(xml_file):
    transactions = []
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for sms in root.findall('sms'):
        body = sms.find('body').text
        if not body:
            logging.warning(f"Empty SMS body: {ET.tostring(sms, encoding='unicode')}")
            continue

        transaction = {
            'id': str(uuid.uuid4()),
            'type': categorize_transaction(body),
            'amount': parse_amount(body),
            'name': parse_name(body),
            'phone': parse_phone_number(body),
            'transaction_id': parse_transaction_id(body),
            'date': parse_date(body),
            'fees': None
        }

        if None in [transaction['type'], transaction['amount'], transaction['date']]:
            logging.warning(f"Unprocessable SMS: {body}")
            continue

        transactions.append(transaction)

    with open('unprocessed_sms.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['SMS Body'])
        for record in logging.getLogger().handlers[0].buffer:
            if record.levelname == 'WARNING':
                writer.writerow([record.msg])

    return transactions