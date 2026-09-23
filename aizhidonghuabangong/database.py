# database.py 同步数据库配置，适配Render Postgres
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 读取Render环境变量 Internal Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """自动创建数据表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """数据库依赖项，接口调用自动获取session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
