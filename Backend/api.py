
import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="MoMo SMS Analytics API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'momo.db')

# Pydantic models for response validation
class Transaction(BaseModel):
    id: int
    transaction_id: Optional[str]
    transaction_type: str
    amount: Optional[float]
    currency: str
    sender_name: Optional[str]
    receiver_name: Optional[str]
    phone_number: Optional[str]
    agent_name: Optional[str]
    agent_code: Optional[str]
    transaction_date: Optional[str]
    fees: Optional[float]
    balance_after: Optional[float]
    raw_sms_body: str
    created_at: str
    updated_at: str

class Summary(BaseModel):
    transaction_type: str
    transaction_count: int
    total_amount: Optional[float]
    average_amount: Optional[float]
    min_amount: Optional[float]
    max_amount: Optional[float]
    total_fees: Optional[float]

class MonthlySummary(BaseModel):
    month: str
    transaction_type: str
    count: int
    total_amount: Optional[float]
    total_fees: Optional[float]

# Database dependency
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Validate transaction type
async def get_valid_types(conn: sqlite3.Connection) -> set:
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM transaction_categories")
    return {row['category_name'] for row in cursor.fetchall()}

@app.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    transaction_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    phone_number: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """
    Fetch transactions with optional filters for type, date range, phone number, and pagination.
    """
    try:
        cursor = db.cursor()
        query = """
            SELECT id, transaction_id, transaction_type, amount, currency,
                   sender_name, receiver_name, phone_number, agent_name,
                   agent_code, transaction_date, fees, balance_after,
                   raw_sms_body, created_at, updated_at
            FROM transactions WHERE 1=1
        """
        params = []

        # Validate transaction_type
        if transaction_type:
            valid_types = await get_valid_types(db)
            if transaction_type not in valid_types:
                raise HTTPException(status_code=400, detail=f"Invalid transaction type: {transaction_type}")
            query += " AND transaction_type = ?"
            params.append(transaction_type)

        # Validate and apply date range
        try:
            if date_from:
                datetime.strptime(date_from, '%Y-%m-%d')
                query += " AND date(transaction_date) >= ?"
                params.append(date_from)
            if date_to:
                datetime.strptime(date_to, '%Y-%m-%d')
                query += " AND date(transaction_date) <= ?"
                params.append(date_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        # Apply phone number filter
        if phone_number:
            query += " AND phone_number LIKE ?"
            params.append(f"%{phone_number}%")

        # Apply pagination
        query += " ORDER BY transaction_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        logger.info(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        transactions = [dict(row) for row in cursor.fetchall()]
        return transactions

    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/summary", response_model=List[Summary])
async def get_summary(db: sqlite3.Connection = Depends(get_db_connection)):
    """
    Fetch transaction summary from the transaction_summary view.
    """
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM transaction_summary")
        summary = [dict(row) for row in cursor.fetchall()]
        return summary
    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/monthly", response_model=List[MonthlySummary])
async def get_monthly_summary(db: sqlite3.Connection = Depends(get_db_connection)):
    """
    Fetch monthly summary from the monthly_summary view.
    """
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM monthly_summary")
        monthly = [dict(row) for row in cursor.fetchall()]
        return monthly
    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
