# routers/customers.py — 客户管理接口
# 提供客户的新增、编辑、查询、删除功能

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select

from database import get_db
from models import Customer
from schemas import CustomerCreate, CustomerResponse
from auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["客户管理"])


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    keyword: Optional[str] = Query(None, description="搜索关键词（客户名称/联系人）"),
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """
    查询客户列表
    支持按客户名称或联系人模糊搜索
    """
    query = select(Customer).order_by(Customer.created_at.desc())

    # 如果有关键词，添加模糊搜索条件
    if keyword:
        query = query.where(
            Customer.name.contains(keyword) | Customer.contact.contains(keyword)
        )

    result = db.execute(query)
    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """查询单个客户详情"""
    result = db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """新增客户"""
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.flush()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    data: CustomerCreate,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """编辑客户信息"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 更新字段
    for key, value in data.model_dump().items():
        setattr(customer, key, value)

    await db.flush()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """删除客户"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    await db.delete(customer)
    return {"message": "删除成功"}
