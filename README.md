# Risk Warning System - 保险资产管理风险预警系统

## 技术栈
- 后端: Python Django + Django REST Framework
- 前端: React + Ant Design
- 数据库: PostgreSQL
- 缓存: Redis
- 任务队列: Celery

## 功能模块

### 1. 认证模块
- JWT登录认证
- 用户权限控制
- 角色管理

### 2. 风险监控
- 组合风险拨测
- 交易实时监控
- 投前风险评估
- 投后持仓监控

### 3. 数据缓存
- Redis热点数据缓存
- 缓存过期管理

### 4. 定时任务
- 定时数据同步
- 定时报表导出
- 风险指标计算

### 5. 预警通知
- 风险阈值预警
- 邮件/短信/企业微信推送

## 快速启动

### 后端
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 启动服务
python manage.py runserver 0.0.0.0:8000
```

### 前端
```bash
cd frontend
npm install
npm start
```

### Celery定时任务
```bash
celery -A risk_project worker -l info
celery -A risk_project beat -l info
```

## 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# 数据库
DB_NAME=risk_db
DB_USER=risk_user
DB_PASSWORD=risk_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_URL=redis://localhost:6379/2

# 邮件配置
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your-email-password

# 企业微信
WECHAT_CORPID=your-corpid
WECHAT_AGENTID=your-agentid
WECHAT_SECRET=your-secret
```

## 项目结构

```
risk/
├── backend/
│   ├── accounts/          # 用户认证模块
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── permissions.py
│   ├── risk/              # 风险监控模块
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── serializers.py
│   ├── tasks/             # 定时任务模块
│   │   ├── tasks.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── risk_project/      # Django项目配置
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── celery.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── stores/
│   │   └── App.js
│   ├── public/
│   ├── package.json
│   └── README.md
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/api/docs/
- Redoc: http://localhost:8000/api/redoc/

## 许可证
MIT
