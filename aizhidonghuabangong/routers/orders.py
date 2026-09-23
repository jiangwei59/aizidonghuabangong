# routers/orders.py — 订单管理接口
# 提供订单的新增、编辑、查询、删除功能，订单编号自动生成

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select, func

from database import get_db
from models import Order, Customer
from schemas import OrderCreate, OrderResponse
from auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


def generate_order_no(db) -> str:
    """
    自动生成订单编号
    格式：ORD-YYYYMMDD-XXXX（如 ORD-20260922-0001）
    每天从 0001 开始编号
    """
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"ORD-{today_str}-"

    # 查询今天已有订单中最大的编号
    result = db.execute(
        select(func.max(Order.order_no)).where(Order.order_no.like(f"{prefix}%"))
    )
    max_no = result.scalar()

    if max_no:
        # 提取序号部分并加 1
        seq = int(max_no.split("-")[-1]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    keyword: Optional[str] = Query(None, description="搜索关键词（订单编号/客户名称）"),
    status: Optional[str] = Query(None, description="订单状态筛选"),
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """
    查询订单列表
    支持按订单编号或客户名称搜索，支持按状态筛选
    """
    query = select(Order).join(Customer).order_by(Order.created_at.desc())

    # 关键词搜索
    if keyword:
        query = query.where(
            Order.order_no.contains(keyword) | Customer.name.contains(keyword)
        )

    # 状态筛选
    if status:
        query = query.where(Order.status == status)

    result = await db.execute(query)
    orders = result.scalars().all()

    # 补充客户名称字段
    order_list = []
    for order in orders:
        # 查询关联的客户名称
        cust_result = await db.execute(select(Customer.name).where(Customer.id == order.customer_id))
        cust_name = cust_result.scalar_one_or_none()
        order_data = OrderResponse.model_validate(order)
        order_data.customer_name = cust_name
        order_list.append(order_data)

    return order_list


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """查询单个订单详情"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 查询客户名称
    cust_result = await db.execute(select(Customer.name).where(Customer.id == order.customer_id))
    order_data = OrderResponse.model_validate(order)
    order_data.customer_name = cust_result.scalar_one_or_none()
    return order_data


@router.post("", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """
    新增订单
    订单编号自动生成，无需前端传入
    """
    # 验证客户是否存在
    cust_result = await db.execute(select(Customer).where(Customer.id == data.customer_id))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=400, detail="关联客户不存在")

    # 生成订单编号
    order_no = generate_order_no(db)

    order = Order(
        order_no=order_no,
        **data.model_dump()
    )
    db.add(order)
    db.flush()
    db.refresh(order)

    order_data = OrderResponse.model_validate(order)
    order_data.customer_name = customer.name
    return order_data


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    data: OrderCreate,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """编辑订单（订单编号不可修改）"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 更新字段（不包括 order_no）
    order.customer_id = data.customer_id
    order.amount = data.amount
    order.product_info = data.product_info
    order.delivery_date = data.delivery_date
    if data.status:
        order.status = data.status

    await db.flush()
    await db.refresh(order)

    # 查询客户名称
    cust_result = await db.execute(select(Customer.name).where(Customer.id == order.customer_id))
    order_data = OrderResponse.model_validate(order)
    order_data.customer_name = cust_result.scalar_one_or_none()
    return order_data


@router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    db = Depends(get_db),
    _user=Depends(get_current_user)
):
    """删除订单"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    await db.delete(order)
    return {"message": "删除成功"}
