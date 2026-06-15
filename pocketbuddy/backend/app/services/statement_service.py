"""Bank statement processing service."""

import io
from datetime import date
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.financial import BankStatement, Expense


async def process_bank_statement(file: UploadFile, user_id: str, db: AsyncSession) -> dict:
    """Process uploaded bank statement PDF."""
    import PyPDF2

    # Read PDF content
    content = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

    raw_text = ""
    for page in pdf_reader.pages:
        raw_text += page.extract_text() + "\n"

    # Save statement record
    statement = BankStatement(
        user_id=user_id,
        filename=file.filename,
        file_path=f"statements/{user_id}/{file.filename}",
        processed="processing",
        raw_text=raw_text,
    )
    db.add(statement)
    await db.flush()

    # Use AI to extract transactions
    transactions = await _extract_transactions_ai(raw_text)

    # Create expense records
    expenses_created = 0
    for txn in transactions:
        try:
            expense = Expense(
                user_id=user_id,
                amount=abs(float(txn.get("amount", 0))),
                category=txn.get("category", "other"),
                description=txn.get("description", ""),
                merchant=txn.get("merchant"),
                date=_parse_date(txn.get("date", str(date.today()))),
                source="statement",
                is_essential=txn.get("is_essential", "unknown"),
            )
            db.add(expense)
            expenses_created += 1
        except (ValueError, TypeError):
            continue

    statement.processed = "completed"
    statement.transactions_extracted = expenses_created
    await db.flush()

    return {
        "status": "completed",
        "filename": file.filename,
        "transactions_extracted": expenses_created,
        "message": f"Successfully extracted {expenses_created} transactions from your statement.",
    }


async def _extract_transactions_ai(raw_text: str) -> list:
    """Use AI to extract structured transactions from statement text."""
    import google.generativeai as genai
    import json

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")

    # Truncate text if too long
    text_preview = raw_text[:4000]

    prompt = f"""Extract financial transactions from this bank statement text.
For each transaction, determine:
- date (YYYY-MM-DD format)
- amount (positive number)
- description (brief)
- merchant (if identifiable)
- category (food, shopping, travel, entertainment, education, health, rent, utilities, groceries, subscriptions, other)
- is_essential (essential or discretionary)

Bank statement text:
{text_preview}

Return ONLY a JSON array of transaction objects. If no transactions found, return empty array [].
Focus on debit/expense transactions only."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text.strip())
    except Exception:
        return []


def _parse_date(date_str: str) -> date:
    """Parse various date formats."""
    from dateutil import parser
    try:
        return parser.parse(date_str).date()
    except (ValueError, TypeError):
        return date.today()
