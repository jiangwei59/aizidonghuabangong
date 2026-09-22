# main.py — FastAPI 应用主入口
# 小微企业自动化办公系统

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db, async_session
from auth import hash_password
from models import User
from sqlalchemy import select

# 导入路由模块
from routers import customers, orders, followups, documents, alerts


async def create_default_admin():
    """
    创建默认管理员账号（如果不存在）
    默认账号：admin / admin123
    生产环境请务必修改密码
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none() is None:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123")
            )
            session.add(admin)
            await session.commit()
            print("[OK] Default admin created: admin / admin123")
        else:
            print("[OK] Admin user already exists")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时：自动建表 + 创建默认管理员
    """
    print("[START] Initializing database...")
    await init_db()
    await create_default_admin()
    print("[OK] Database initialized")
    yield
    print("[STOP] Application shutdown")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="小微企业自动化办公系统",
    description="客户管理、订单管理、跟进记录、文档生成、异常提醒",
    version="1.0.0",
    lifespan=lifespan
)

# ========== 配置 CORS ==========
# 允许前端静态页面访问后端接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境可限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 挂载路由 ==========
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(followups.router)
app.include_router(documents.router)
app.include_router(alerts.router)


# ========== 登录接口（放在 main.py 中，不单独建路由） ==========
from fastapi import Depends
from schemas import UserLogin, TokenResponse
from auth import verify_password, create_access_token
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


@app.post("/api/login", response_model=TokenResponse, tags=["登录"])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    管理员登录接口
    验证用户名密码，返回 JWT Token
    """
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=token)


# ========== 挂载静态文件 ==========
# 前端页面放在 static 目录，访问根路径即可打开
app.mount("/", StaticFiles(directory="static", html=True), name="static")