# 小微企业自动化办公系统 — 部署文档

## 一、技术栈

| 组件 | 技术 |
|------|------|
| 前端 | 原生 HTML + JavaScript + CSS |
| 后端 | Python FastAPI |
| 数据库 | Render 内置 PostgreSQL |
| 部署平台 | Render Web Service |

## 二、部署步骤

### 步骤 1：创建 Render 账号

1. 访问 [https://render.com](https://render.com)
2. 使用 GitHub 账号注册并登录

### 步骤 2：创建 PostgreSQL 数据库

1. 在 Render Dashboard 点击 **New → PostgreSQL**
2. 设置如下：
   - **Name**: `office-db`
   - **Database**: `office_automation`
   - **Plan**: Free（免费套餐）
3. 点击 **Create Database**
4. 创建完成后，进入数据库详情页，复制 **Internal Database URL**（格式类似 postgresql://office_automation_9lk3_user:9XddxJw4gcvCwTMj090HhVkqZGZJT7bP@dpg-daooj0lg1s2s73926hv0-a/office_automation_9lk3）

### 步骤 3：创建 Web Service

1. 在 Render Dashboard 点击 **New → Web Service**
2. 连接你的 GitHub 仓库（需要先将项目代码推送到 GitHub）
3. 设置如下：
   - **Name**: `office-automation`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. 在 **Environment Variables** 中添加：
   - `DATABASE_URL` = 步骤 2 中复制的数据库连接字符串
   - `SECRET_KEY` = 任意随机字符串（如 `my-secret-key-2026`）
5. 点击 **Create Web Service**

### 步骤 4：访问系统

1. 部署完成后，Render 会分配一个域名（如 `https://office-automation.onrender.com`）
2. 在浏览器中打开该域名
3. 使用默认管理员账号登录：
   - **用户名**: `admin`
   - **密码**: `admin123`

## 三、本地开发

### 环境要求

- Python 3.11+
- pip

### 启动步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量（可选，不设置则使用本地 SQLite）
# Windows PowerShell:
$env:DATABASE_URL="postgresql+asyncpg://用户名:密码@localhost:5432/数据库名"
# Linux/Mac:
export DATABASE_URL="postgresql+asyncpg://用户名:密码@localhost:5432/数据库名"

# 3. 启动服务
uvicorn main:app --reload

# 4. 访问 http://localhost:8000
```

## 四、系统测试步骤

### 测试 1：登录
1. 打开系统首页
2. 输入用户名 `admin`，密码 `admin123`
3. 点击登录，应跳转到主界面

### 测试 2：新增客户
1. 点击顶部导航「客户管理」
2. 点击「+ 新增客户」
3. 填写客户信息：
   - 客户名称：测试客户A
   - 联系人：张三
   - 电话：13800138000
   - 地址：北京市朝阳区
4. 点击保存，客户列表中应显示新客户

### 测试 3：新增订单
1. 点击顶部导航「订单管理」
2. 点击「+ 新增订单」
3. 选择关联客户（测试客户A）
4. 填写订单信息：
   - 金额：10000
   - 商品信息：办公用品一批
   - 交货时间：选择一周后的日期
5. 点击保存，订单编号应自动生成（格式：ORD-日期-序号）

### 测试 4：跟进记录
1. 点击顶部导航「跟进记录」
2. 点击「+ 新增跟进」
3. 选择客户，填写跟进内容
4. 点击保存，记录列表中应显示新记录

### 测试 5：文档导出
1. 点击顶部导航「文档导出」
2. 找到刚才创建的订单
3. 点击「下载 Word」
4. 浏览器应下载一个 Word 文档，包含订单和客户信息

### 测试 6：异常提醒
1. 点击顶部导航「异常提醒」
2. 应看到：
   - 到期订单：如果订单交货日期在 7 天内，会显示在提醒列表
   - 待跟进客户：新客户如果没有跟进记录，会显示在提醒列表

## 五、项目文件说明

```
├── main.py              # FastAPI 主入口
├── database.py          # 数据库连接配置
├── models.py            # 数据库模型（表结构）
├── schemas.py           # Pydantic 数据校验模型
├── auth.py              # 登录鉴权（JWT Token）
├── requirements.txt     # Python 依赖
├── render.yaml          # Render 部署配置
├── Procfile             # 进程启动命令
├── routers/
│   ├── customers.py     # 客户管理接口
│   ├── orders.py        # 订单管理接口
│   ├── followups.py     # 跟进记录接口
│   ├── documents.py     # 文档生成接口
│   └── alerts.py        # 异常提醒接口
└── static/
    ├── index.html       # 前端主页面
    ├── css/style.css    # 样式文件
    └── js/
        ├── api.js       # API 请求封装
        └── app.js       # 前端业务逻辑
```

## 六、注意事项

1. **数据库连接**：所有数据库信息从环境变量 `DATABASE_URL` 获取，禁止硬编码
2. **密码安全**：默认管理员密码为 `admin123`，生产环境请及时修改
3. **CORS 配置**：已配置允许所有来源访问，生产环境可限制为具体域名
4. **免费套餐限制**：Render 免费套餐在无请求时会休眠，首次访问可能需要等待 30 秒
5. **自动建表**：首次启动时自动创建数据库表和默认管理员账号，无需手动导入 SQL