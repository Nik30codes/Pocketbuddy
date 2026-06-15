"""Financial endpoints: expenses, income, budgets, statements."""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.financial import Expense, Income, Budget, BankStatement, ExpenseCategory
from app.schemas.financial import (
    ExpenseCreate,
    ExpenseResponse,
    IncomeCreate,
    IncomeResponse,
    BudgetCreate,
    BudgetResponse,
    FinancialSummary,
    ConversationalExpense,
)

router = APIRouter()


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    data: ExpenseCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense entry."""
    expense = Expense(
        user_id=user_id,
        amount=data.amount,
        category=data.category,
        description=data.description,
        merchant=data.merchant,
        date=data.date,
        is_essential=data.is_essential,
        source="manual",
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return expense


@router.get("/expenses", response_model=List[ExpenseResponse])
async def get_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user expenses with optional filters."""
    query = select(Expense).where(Expense.user_id == user_id)

    if start_date:
        query = query.where(Expense.date >= start_date)
    if end_date:
        query = query.where(Expense.date <= end_date)
    if category:
        query = query.where(Expense.category == category)

    query = query.order_by(Expense.date.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/income", response_model=IncomeResponse, status_code=201)
async def create_income(
    data: IncomeCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new income entry."""
    income = Income(
        user_id=user_id,
        amount=data.amount,
        source=data.source,
        description=data.description,
        date=data.date,
        is_recurring=data.is_recurring,
    )
    db.add(income)
    await db.flush()
    await db.refresh(income)
    return income


@router.get("/income", response_model=List[IncomeResponse])
async def get_income(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user income entries."""
    result = await db.execute(
        select(Income).where(Income.user_id == user_id).order_by(Income.date.desc())
    )
    return result.scalars().all()


@router.post("/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    data: BudgetCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a budget for a category."""
    # Check if budget exists for this category/month
    result = await db.execute(
        select(Budget).where(
            and_(
                Budget.user_id == user_id,
                Budget.category == data.category,
                Budget.month == data.month,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.monthly_limit = data.monthly_limit
        await db.flush()
        await db.refresh(existing)
        return existing

    budget = Budget(
        user_id=user_id,
        category=data.category,
        monthly_limit=data.monthly_limit,
        month=data.month,
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


@router.get("/budgets", response_model=List[BudgetResponse])
async def get_budgets(
    month: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user budgets."""
    query = select(Budget).where(Budget.user_id == user_id)
    if month:
        query = query.where(Budget.month == month)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/summary", response_model=FinancialSummary)
async def get_financial_summary(
    month: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get financial summary for the current or specified month."""
    from app.services.financial_service import calculate_financial_summary

    # Trigger notification engine on financial page load
    from app.services.notification_engine import generate_notifications
    await generate_notifications(user_id, db)

    return await calculate_financial_summary(user_id, month, db)


@router.post("/expenses/conversational", response_model=ExpenseResponse)
async def log_conversational_expense(
    data: ConversationalExpense,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log expense from natural language input."""
    from app.services.ai_service import parse_conversational_expense
    expense_data = await parse_conversational_expense(data.message, user_id)

    expense = Expense(
        user_id=user_id,
        amount=expense_data["amount"],
        category=expense_data["category"],
        description=expense_data["description"],
        merchant=expense_data.get("merchant"),
        date=expense_data.get("date", date.today()),
        source="conversational",
        is_essential=expense_data.get("is_essential", "unknown"),
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return expense


@router.post("/statements/upload")
async def upload_bank_statement(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a bank statement PDF."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    from app.services.statement_service import process_bank_statement
    result = await process_bank_statement(file, user_id, db)
    return result
