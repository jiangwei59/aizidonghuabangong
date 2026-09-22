# schemas.py — Pydantic 请求/响应模型
# 定义接口的输入输出数据格式，用于参数校验和序列化

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


# ========== 用户相关 ==========

class UserLogin(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """登录成功返回 Token"""
    access_token: str
    token_type: str = "bearer"


# ========== 客户相关 ==========

class CustomerCreate(BaseModel):
    """新增/编辑客户请求"""
    name: str  # 客户名称（必填）
    contact: Optional[str] = None  # 联系人
    phone: Optional[str] = None  # 电话
    address: Optional[str] = None  # 地址
    notes: Optional[str] = None  # 备注


class CustomerResponse(BaseModel):
    """客户信息响应"""
    id: int
    name: str
    contact: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 SQLAlchemy 模型转换


# ========== 订单相关 ==========

class OrderCreate(BaseModel):
    """新增/编辑订单请求"""
    customer_id: int  # 关联客户ID（必填）
    amount: float = 0  # 订单金额
    product_info: Optional[str] = None  # 商品信息
    delivery_date: Optional[date] = None  # 交货时间
    status: Optional[str] = "待处理"  # 订单状态


class OrderResponse(BaseModel):
    """订单信息响应"""
    id: int
    order_no: str
    customer_id: int
    amount: float
    product_info: Optional[str]
    delivery_date: Optional[date]
    status: str
    created_at: datetime
    # 关联客户名称（方便前端显示）
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True


# ========== 跟进记录相关 ==========

class FollowUpCreate(BaseModel):
    """新增跟进记录请求"""
    customer_id: int  # 关联客户ID（必填）
    content: str  # 跟进内容（必填）
    follow_time: Optional[datetime] = None  # 跟进时间（默认当前时间）


class FollowUpResponse(BaseModel):
    """跟进记录响应"""
    id: int
    customer_id: int
    content: str
    follow_time: datetime
    created_at: datetime
    # 关联客户名称
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True


# ========== 提醒相关 ==========

class AlertItem(BaseModel):
    """异常提醒项"""
    type: str  # 提醒类型：到期订单 / 待跟进客户
    title: str  # 提醒标题
    detail: str  # 提醒详情
    related_id: int  # 关联的订单或客户ID
    date: Optional[str] = None  # 相关日期


class AlertResponse(BaseModel):
    """异常提醒响应"""
    due_orders: List[AlertItem]  # 到期订单列表
    pending_followups: List[AlertItem]  # 待跟进客户列表
