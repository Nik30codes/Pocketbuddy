"""AI-Powered Notification Engine - generates contextual, data-driven notifications."""

from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.notification import Notification
from app.models.financial import Expense, Income
from app.models.wellness import DailyCheckin
from app.models.user import User


async def generate_notifications(user_id: str, db: AsyncSession) -> list:
    """Run the full notification engine for a user. Returns new notifications generated."""
    new_notifications = []

    # Get user profile
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return []

    # Run all notification generators
    new_notifications += await _budget_alerts(user_id, user, db)
    new_notifications += await _spending_spike_detection(user_id, db)
    new_notifications += await _overspending_prediction(user_id, user, db)
    new_notifications += await _wellness_alerts(user_id, user, db)
    new_notifications += await _burnout_detection(user_id, db)
    new_notifications += await _achievement_notifications(user_id, db)
    new_notifications += await _daily_routine_notification(user_id, user, db)

    return new_notifications


async def _budget_alerts(user_id: str, user: User, db: AsyncSession) -> list:
    """Generate budget utilization warnings at 70%, 85%, 95%."""
    today = date.today()
    month_start = today.replace(day=1)

    # Get total spent
    result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id, Expense.date >= month_start
        )
    )
    total_spent = result.scalar() or 0

    # Get income as fallback budget
    income_result = await db.execute(
        select(func.sum(Income.amount)).where(
            Income.user_id == user_id, Income.date >= month_start
        )
    )
    total_income = income_result.scalar() or 0

    # Use monthly_budget if set, otherwise use income
    budget = user.monthly_budget if user.monthly_budget and user.monthly_budget > 0 else total_income
    if budget <= 0:
        return []

    utilization = (total_spent / budget) * 100
    days_left = max(1, 30 - today.day)
    remaining = budget - total_spent

    # Check if we already sent a budget alert today
    existing = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.notification_type == "financial",
            Notification.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0),
        )
    )
    if existing.scalars().first():
        return []

    notifications = []

    if utilization >= 95:
        n = Notification(
            user_id=user_id,
            title="🚨 Budget Critical",
            message=f"You've used {utilization:.0f}% of your budget (₹{total_spent:,.0f}/₹{budget:,.0f}). Only ₹{max(0,remaining):,.0f} remains for {days_left} days. Essential spending only.",
            notification_type="financial",
            priority="critical",
            action_url="/financial",
        )
        db.add(n)
        notifications.append(n)
    elif utilization >= 85:
        n = Notification(
            user_id=user_id,
            title="⚠️ Budget Warning",
            message=f"You've used {utilization:.0f}% of your budget. ₹{remaining:,.0f} remains for the next {days_left} days. Daily limit: ₹{remaining/days_left:,.0f}.",
            notification_type="financial",
            priority="high",
            action_url="/financial",
        )
        db.add(n)
        notifications.append(n)
    elif utilization >= 70:
        n = Notification(
            user_id=user_id,
            title="📊 Budget Update",
            message=f"70% of your budget used (₹{total_spent:,.0f}/₹{budget:,.0f}). ₹{remaining:,.0f} left. Safe daily spend: ₹{remaining/days_left:,.0f}.",
            notification_type="financial",
            priority="medium",
            action_url="/financial",
        )
        db.add(n)
        notifications.append(n)

    return notifications


async def _spending_spike_detection(user_id: str, db: AsyncSession) -> list:
    """Detect spending spikes by comparing this week to last week."""
    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start

    # This week spending
    result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id, Expense.date >= this_week_start
        )
    )
    this_week = result.scalar() or 0

    # Last week spending
    result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id,
            Expense.date >= last_week_start,
            Expense.date < last_week_end,
        )
    )
    last_week = result.scalar() or 0

    if last_week > 0 and this_week > last_week * 1.25:
        increase = ((this_week - last_week) / last_week) * 100

        # Find top category this week
        cat_result = await db.execute(
            select(Expense.category, func.sum(Expense.amount).label('total'))
            .where(Expense.user_id == user_id, Expense.date >= this_week_start)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
            .limit(1)
        )
        top_cat = cat_result.first()
        cat_name = top_cat[0].value if top_cat and hasattr(top_cat[0], 'value') else str(top_cat[0]) if top_cat else "overall"

        n = Notification(
            user_id=user_id,
            title="📈 Spending Spike Detected",
            message=f"Your spending increased by {increase:.0f}% this week compared to last week. Top category: {cat_name}. Consider reviewing non-essential expenses.",
            notification_type="financial",
            priority="medium",
            action_url="/financial",
        )
        db.add(n)
        return [n]

    return []


async def _overspending_prediction(user_id: str, user: User, db: AsyncSession) -> list:
    """Predict if user will exceed budget by month end."""
    if not user.monthly_budget:
        return []

    today = date.today()
    month_start = today.replace(day=1)
    days_elapsed = (today - month_start).days + 1

    result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id, Expense.date >= month_start
        )
    )
    total_spent = result.scalar() or 0
    daily_avg = total_spent / days_elapsed
    projected = daily_avg * 30
    overshoot = projected - user.monthly_budget

    if overshoot > 0 and days_elapsed >= 7:  # Only predict after 7 days of data
        n = Notification(
            user_id=user_id,
            title="🔮 Overspending Forecast",
            message=f"At your current rate (₹{daily_avg:,.0f}/day), you may exceed your budget by ₹{overshoot:,.0f} this month. Reduce daily spending to ₹{(user.monthly_budget - total_spent) / max(1, 30 - today.day):,.0f} to stay on track.",
            notification_type="prediction",
            priority="high",
            action_url="/financial",
        )
        db.add(n)
        return [n]

    return []


async def _wellness_alerts(user_id: str, user: User, db: AsyncSession) -> list:
    """Generate wellness-based notifications."""
    today = date.today()
    three_days_ago = today - timedelta(days=3)

    result = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= three_days_ago)
        .order_by(DailyCheckin.date.desc())
    )
    checkins = result.scalars().all()

    if len(checkins) < 3:
        return []

    notifications = []

    # Sleep deprivation (< 6 hours for 3 days)
    low_sleep_days = sum(1 for c in checkins if c.sleep_hours < 6)
    if low_sleep_days >= 3:
        avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins)
        n = Notification(
            user_id=user_id,
            title="😴 Sleep Alert",
            message=f"Your average sleep has been {avg_sleep:.1f}h for the past {len(checkins)} days — below your {user.sleep_goal_hours}h goal. Sleep deprivation affects memory, mood, and focus. Prioritize rest tonight.",
            notification_type="wellness",
            priority="high",
            action_url="/wellness",
        )
        db.add(n)
        notifications.append(n)

    # Meal skipping
    avg_meals_skipped = sum(c.meals_skipped for c in checkins) / len(checkins)
    if avg_meals_skipped >= 1.5:
        n = Notification(
            user_id=user_id,
            title="🍽️ Nutrition Alert",
            message=f"You've been skipping an average of {avg_meals_skipped:.1f} meals/day. Regular meals maintain energy and concentration. Even a quick snack counts.",
            notification_type="wellness",
            priority="medium",
            action_url="/wellness",
        )
        db.add(n)
        notifications.append(n)

    return notifications


async def _burnout_detection(user_id: str, db: AsyncSession) -> list:
    """Detect burnout patterns and generate critical alerts."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    result = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= week_ago)
        .order_by(DailyCheckin.date.desc())
    )
    checkins = result.scalars().all()

    if len(checkins) < 5:
        return []

    avg_stress = sum(c.stress_score for c in checkins) / len(checkins)
    avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins)
    avg_study = sum(c.study_hours for c in checkins) / len(checkins)
    high_stress_days = sum(1 for c in checkins if c.stress_score >= 7)

    # Critical: High stress + low sleep + high workload
    if avg_stress >= 7 and avg_sleep < 6 and avg_study > 6:
        n = Notification(
            user_id=user_id,
            title="🔥 Burnout Risk: CRITICAL",
            message=f"Elevated burnout risk detected. Stress at {avg_stress:.1f}/10 for {high_stress_days} days, sleep averaging {avg_sleep:.1f}h with {avg_study:.0f}h study/day. Immediate self-care needed. AI wellness plan available.",
            notification_type="burnout",
            priority="critical",
            action_url="/wellness",
        )
        db.add(n)
        return [n]

    # High: Sustained high stress
    if high_stress_days >= 5:
        n = Notification(
            user_id=user_id,
            title="⚠️ Burnout Warning",
            message=f"Stress has remained high (7+) for {high_stress_days} of the last {len(checkins)} days. Consider taking breaks, reducing workload, or talking to someone.",
            notification_type="burnout",
            priority="high",
            action_url="/wellness",
        )
        db.add(n)
        return [n]

    return []


async def _achievement_notifications(user_id: str, db: AsyncSession) -> list:
    """Generate positive reinforcement achievements."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    result = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= week_ago)
        .order_by(DailyCheckin.date.asc())
    )
    checkins = result.scalars().all()

    notifications = []

    # 7-day streak
    if len(checkins) >= 7:
        n = Notification(
            user_id=user_id,
            title="🏆 7-Day Check-in Streak!",
            message="You've logged daily check-ins for 7 consecutive days! Consistency is key to understanding your patterns. Keep it up!",
            notification_type="achievement",
            priority="low",
            action_url="/wellness",
        )
        db.add(n)
        notifications.append(n)

    # Stress improvement
    if len(checkins) >= 5:
        first_half = checkins[:len(checkins)//2]
        second_half = checkins[len(checkins)//2:]
        if first_half and second_half:
            early_stress = sum(c.stress_score for c in first_half) / len(first_half)
            recent_stress = sum(c.stress_score for c in second_half) / len(second_half)
            if early_stress > 6 and recent_stress < early_stress * 0.8:
                improvement = ((early_stress - recent_stress) / early_stress) * 100
                n = Notification(
                    user_id=user_id,
                    title="📉 Stress Improved!",
                    message=f"Your stress levels decreased by {improvement:.0f}% this week. Whatever you're doing, it's working. Keep maintaining those habits!",
                    notification_type="achievement",
                    priority="low",
                    action_url="/wellness",
                )
                db.add(n)
                notifications.append(n)

    return notifications


async def _daily_routine_notification(user_id: str, user: User, db: AsyncSession) -> list:
    """Generate a morning daily pocket plan notification."""
    # Only generate if it's morning (or first check today)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    existing = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.notification_type == "routine",
            Notification.created_at >= today_start,
        )
    )
    if existing.scalars().first():
        return []

    # Get today's context
    today = date.today()
    month_start = today.replace(day=1)

    result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id, Expense.date >= month_start
        )
    )
    spent = result.scalar() or 0
    remaining = (user.monthly_budget - spent) if user.monthly_budget else None
    daily_budget = remaining / max(1, 30 - today.day) if remaining else None

    # Get latest wellness
    result = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id)
        .order_by(DailyCheckin.date.desc())
        .limit(1)
    )
    last_checkin = result.scalar_one_or_none()

    # Build daily plan message
    parts = ["📋 Today's Pocket Plan\n"]
    if daily_budget:
        parts.append(f"💰 Daily budget: ₹{daily_budget:,.0f}")
    if last_checkin and last_checkin.sleep_hours < 6:
        parts.append(f"😴 You slept {last_checkin.sleep_hours}h — try to rest earlier tonight")
    if last_checkin and last_checkin.stress_score >= 7:
        parts.append(f"🧘 Stress was high yesterday — take 10-min breaks today")
    parts.append(f"🎯 Log a check-in at the end of the day")

    n = Notification(
        user_id=user_id,
        title="🌅 Your Daily Pocket Plan",
        message="\n".join(parts),
        notification_type="routine",
        priority="low",
        action_url="/routine",
    )
    db.add(n)
    return [n]
