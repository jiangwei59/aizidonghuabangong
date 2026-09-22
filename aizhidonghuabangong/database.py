# database.py — 数据库连接配置
# 从环境变量 DATABASE_URL 读取连接信息，禁止硬编码

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 从环境变量获取数据库连接字符串
# Render 部署时自动设置，本地开发可手动设置
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Render 的 PostgreSQL 连接字符串以 postgres:// 开头
# SQLAlchemy 2.x 需要 postgresql+asyncpg:// 前缀
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 如果没有设置环境变量，使用 SQLite 作为本地开发备用
if not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///./local_dev.db"

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=False)

# 创建异步会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 声明模型基类
Base = declarative_base()


async def get_db():
    """
    获取数据库会话的依赖函数
    用于 FastAPI 的 Depends 注入
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库 — 自动创建所有表
    项目启动时调用，不需要手动导入 SQL
    """
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册到 Base.metadata
        import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
