# main.py 小微企业自动化办公系统 主入口（同步SQLAlchemy版本）
from contextlib import contextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from database import get_db, init_db, SessionLocal
from models import User
from schemas import UserLogin, TokenResponse
from auth import hash_password, verify_password, create_access_token

# 导入路由模块
from routers import customers, orders, followups, documents, alerts


def create_default_admin():
    """
    创建默认管理员账号，不存在则新建
    默认账号 admin 密码 admin123，上线务必修改！
    """
    db = SessionLocal()
    try:
        result = db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none() is None:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123")
            )
            db.add(admin)
            db.commit()
            print("[OK] Default admin created: admin / admin123")
        else:
            print("[OK] Admin user already exists")
    finally:
        db.close()


@contextmanager
def lifespan(app: FastAPI):
    """应用生命周期：启动自动建表+创建管理员"""
    print("[START] Initializing database...")
    init_db()
    create_default_admin()
    print("[OK] Database initialized")
    yield
    print("[STOP] Application shutdown")


# 创建FastAPI实例
app = FastAPI(
    title="小微企业自动化办公系统",
    description="客户管理、订单管理、跟进记录、文档生成、异常提醒",
    version="1.0.0",
    lifespan=lifespan
)

# CORS跨域配置，前端html静态页面访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载各个业务路由
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(followups.router)
app.include_router(documents.router)
app.include_router(alerts.router)


# 登录接口
@app.post("/api/login", response_model=TokenResponse, tags=["登录"])
def login(data: UserLogin, db = Depends(get_db)):
    result = db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=token)


# 挂载静态HTML前端页面，访问根路径打开网页
app.mount("/", StaticFiles(directory="static", html=True), name="static")

