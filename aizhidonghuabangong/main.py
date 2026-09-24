from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="小微企业办公系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 暂时注释所有业务路由
# from routers import order,customer,follow
# app.include_router(order.router)
# app.include_router(customer.router)
# app.include_router(follow.router)

@app.get("/")
def index():
    return {"msg":"服务正常"}
