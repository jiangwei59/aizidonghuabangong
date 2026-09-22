# models.py — SQLAlchemy 数据模型定义
# 定义所有数据库表结构

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """管理员用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")


class Customer(Base):
    """客户信息表"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="客户名称")
    contact = Column(String(50), comment="联系人")
    phone = Column(String(20), comment="电话")
    address = Column(String(200), comment="地址")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.now, comment="录入时间")

    # 关联订单和跟进记录
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="customer", cascade="all, delete-orphan")


class Order(Base):
    """订单信息表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(30), unique=True, index=True, nullable=False, comment="订单编号（自动生成）")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="关联客户ID")
    amount = Column(Float, default=0, comment="订单金额")
    product_info = Column(Text, comment="商品信息")
    delivery_date = Column(Date, comment="交货时间")
    status = Column(String(20), default="待处理", comment="订单状态：待处理/生产中/已发货/已完成/已取消")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联客户
    customer = relationship("Customer", back_populates="orders")


class FollowUp(Base):
    """客户跟进记录表"""
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="关联客户ID")
    content = Column(Text, nullable=False, comment="跟进内容")
    follow_time = Column(DateTime, default=datetime.now, comment="跟进时间")
    created_at = Column(DateTime, default=datetime.now, comment="记录创建时间")

    # 关联客户
    customer = relationship("Customer", back_populates="followups")
