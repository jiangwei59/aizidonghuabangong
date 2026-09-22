# routers/followups.py — 客户跟进记录接口
# 提供跟进记录的新增、查询功能，绑定对应客户

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import FollowUp, Customer
from schemas import FollowUpCreate, FollowUpResponse
from auth import get_current_user

router = APIRouter(prefix="/api/followups", tags=["跟进记录"])


@router.get("", response_model=list[FollowUpResponse])
async def list_followups(
    customer_id: Optional[int] = Query(None, description="按客户ID筛选"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user)
):
    """
    查询跟进记录列表
    可按客户ID筛选，返回最近的记录在前
    """
    query = select(FollowUp).order_by(FollowUp.follow_time.desc())

    if customer_id:
        query = query.where(FollowUp.customer_id == customer_id)

    result = await db.execute(query)
    followups = result.scalars().all()

    # 补充客户名称
    followup_list = []
    for fu in followups:
        cust_result = await db.execute(select(Customer.name).where(Customer.id == fu.customer_id))
        fu_data = FollowUpResponse.model_validate(fu)
        fu_data.customer_name = cust_result.scalar_one_or_none()
        followup_list.append(fu_data)

    return followup_list


@router.post("", response_model=FollowUpResponse)
async def create_followup(
    data: FollowUpCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user)
):
    """
    新增跟进记录
    绑定对应客户，记录跟进内容和时间
    """
    # 验证客户是否存在
    cust_result = await db.execute(select(Customer).where(Customer.id == data.customer_id))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=400, detail="关联客户不存在")

    followup = FollowUp(
        customer_id=data.customer_id,
        content=data.content,
        follow_time=data.follow_time or datetime.now()
    )
    db.add(followup)
    await db.flush()
    await db.refresh(followup)

    fu_data = FollowUpResponse.model_validate(followup)
    fu_data.customer_name = customer.name
    return fu_data


@router.delete("/{followup_id}")
async def delete_followup(
    followup_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user)
):
    """删除跟进记录"""
    result = await db.execute(select(FollowUp).where(FollowUp.id == followup_id))
    followup = result.scalar_one_or_none()
    if not followup:
        raise HTTPException(status_code=404, detail="跟进记录不存在")

    await db.delete(followup)
    return {"message": "删除成功"}
