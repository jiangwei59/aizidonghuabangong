# routers/alerts.py — 异常提醒接口
# 查询到期订单和待跟进客户，生成提醒列表

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Order, Customer, FollowUp
from schemas import AlertItem, AlertResponse
from auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["异常提醒"])


@router.get("", response_model=AlertResponse)
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user)
):
    """
    获取异常提醒列表
    - 到期订单：交货日期在 7 天内且未完成的订单
    - 待跟进客户：超过 30 天没有跟进记录的客户
    """
    now = datetime.now()
    due_date_limit = now.date() + timedelta(days=7)  # 7 天内到期
    followup_limit = now - timedelta(days=30)  # 30 天未跟进

    due_orders = []
    pending_followups = []

    # ===== 查询到期订单 =====
    # 条件：交货日期在 7 天内，且状态不是"已完成"或"已取消"
    order_query = (
        select(Order)
        .where(Order.delivery_date != None)
        .where(Order.delivery_date <= due_date_limit)
        .where(Order.status.notin_(["已完成", "已取消"]))
        .order_by(Order.delivery_date)
    )
    order_result = await db.execute(order_query)
    orders = order_result.scalars().all()

    for order in orders:
        # 查询客户名称
        cust_result = await db.execute(select(Customer.name).where(Customer.id == order.customer_id))
        cust_name = cust_result.scalar_one_or_none()

        # 计算剩余天数
        days_left = (order.delivery_date - now.date()).days
        if days_left < 0:
            detail = f"已逾期 {abs(days_left)} 天"
        elif days_left == 0:
            detail = "今日到期"
        else:
            detail = f"还有 {days_left} 天到期"

        due_orders.append(AlertItem(
            type="到期订单",
            title=f"订单 {order.order_no}",
            detail=f"客户：{cust_name} | {detail} | 金额：¥{order.amount:,.2f}",
            related_id=order.id,
            date=str(order.delivery_date)
        ))

    # ===== 查询待跟进客户 =====
    # 查找所有客户
    all_customers_result = await db.execute(select(Customer))
    all_customers = all_customers_result.scalars().all()

    for customer in all_customers:
        # 查询该客户最近一次跟进记录
        last_followup_result = await db.execute(
            select(FollowUp)
            .where(FollowUp.customer_id == customer.id)
            .order_by(FollowUp.follow_time.desc())
            .limit(1)
        )
        last_followup = last_followup_result.scalar_one_or_none()

        # 判断是否需要跟进：无跟进记录 或 最近跟进超过 30 天
        needs_followup = False
        if last_followup is None:
            needs_followup = True
            detail = "从未跟进"
        elif last_followup.follow_time < followup_limit:
            needs_followup = True
            days_since = (now - last_followup.follow_time).days
            detail = f"已 {days_since} 天未跟进"

        if needs_followup:
            pending_followups.append(AlertItem(
                type="待跟进客户",
                title=customer.name,
                detail=f"联系人：{customer.contact or '无'} | {detail}",
                related_id=customer.id,
                date=last_followup.follow_time.strftime("%Y-%m-%d") if last_followup else None
            ))

    return AlertResponse(
        due_orders=due_orders,
        pending_followups=pending_followups
    )
