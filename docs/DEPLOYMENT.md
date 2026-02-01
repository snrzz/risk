# 部署文档

## 环境要求

### 最低配置
- CPU: 2核
- 内存: 4GB
- 存储: 20GB

### 推荐配置
- CPU: 4核
- 内存: 8GB
- 存储: 50GB SSD

## 软件依赖

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (生产环境)
- Redis 7+ (可选，用于缓存和Celery)
- Nginx (反向代理)

## 快速部署

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/snrzz/risk.git
cd risk

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 方式二：手动部署

#### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
npm run build
cd ..
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

#### 3. 数据库配置

```bash
# 创建数据库
sudo -u postgres psql
CREATE DATABASE risk_db;
CREATE USER risk_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE risk_db TO risk_user;
ALTER DATABASE risk_db OWNER TO risk_user;
\q
```

#### 4. 初始化数据库

```bash
# 执行迁移
python manage.py migrate

# 创建管理员账户
python manage.py createsuperuser

# 初始化权限数据
python manage.py shell -c "
from accounts.models import Permission, Role
permissions_data = [
    ('用户管理', 'user_manage', 'user', 'manage'),
    ('角色管理', 'role_manage', 'role', 'manage'),
    ('组合管理', 'portfolio_manage', 'portfolio', 'manage'),
    ('交易查看', 'trade_read', 'trade', 'read'),
    ('风险查看', 'risk_read', 'risk', 'read'),
    ('预警处理', 'alert_manage', 'alert', 'manage'),
    ('任务管理', 'task_manage', 'task', 'manage'),
]
for name, code, resource, action in permissions_data:
    Permission.objects.get_or_create(code=code, defaults={
        'name': name, 'resource_type': resource, 'action_type': action
    })
print('权限初始化完成')
"
```

#### 5. 收集静态文件

```bash
python manage.py collectstatic
```

#### 6. 启动服务

```bash
# 启动Django
gunicorn risk_project.wsgi:application --bind 0.0.0.0:8000

# 启动Celery Worker
celery -A risk_project worker -l info

# 启动Celery Beat
celery -A risk_project beat -l info
```

## Docker部署详细配置

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: risk_db
      POSTGRES_USER: risk_user
      POSTGRES_PASSWORD: risk_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
```

### Nginx配置

```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://frontend;
        }

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## 生产环境配置

### 1. 安全配置

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# 使用HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 2. 性能配置

```python
# 使用Redis缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
    }
}

# Celery配置
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
```

### 3. 日志配置

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/risk/django.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## 验证部署

### 1. 检查服务状态

```bash
# 检查Django
curl http://localhost:8000/api/risk/dashboard/

# 检查前端
curl http://localhost:3000
```

### 2. 登录验证

```bash
# 获取Token
curl -X POST http://localhost:8000/api/token/ \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"admin123"}'

# 使用Token访问API
curl http://localhost:8000/api/accounts/users/me/ \
    -H "Authorization: Bearer <access_token>"
```

## 定时任务配置

### Celery Beat调度

```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-risk-indicators-daily': {
        'task': 'tasks.sync_risk_indicators',
        'schedule': crontab(hour=6, minute=0),
    },
    'check-risk-alerts-hourly': {
        'task': 'tasks.check_risk_alerts',
        'schedule': crontab(minute=0),
    },
    'export-daily-report': {
        'task': 'tasks.export_daily_report',
        'schedule': crontab(hour=18, minute=0),
    },
}
```

## 备份与恢复

### 数据库备份

```bash
# 备份
pg_dump -U risk_user risk_db > backup_$(date +%Y%m%d).sql

# 恢复
psql -U risk_user risk_db < backup_20250117.sql
```

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backup/risk
pg_dump -U risk_user risk_db > $BACKUP_DIR/db_$DATE.sql

# 保留最近7天备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

## 监控

### Health Check

```bash
# Django健康检查
curl http://localhost:8000/health/

# Celery健康检查
celery -A risk_project inspect ping
```

### 日志监控

```bash
# 查看错误日志
tail -f /var/log/risk/django.log | grep ERROR
```

## 故障排查

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose ps db
   # 检查连接
   psql -h localhost -U risk_user -d risk_db
   ```

2. **Celery任务不执行**
   ```bash
   # 检查Worker状态
   celery -A risk_project worker -l info
   # 检查Beat状态
   celery -A risk_project beat -l info
   ```

3. **前端无法连接后端**
   ```bash
   # 检查Nginx配置
   nginx -t
   # 重启Nginx
   docker-compose restart nginx
   ```

## 升级步骤

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt
cd frontend && npm install && npm run build

# 执行迁移
python manage.py migrate

# 重启服务
docker-compose restart
```

## 联系支持

如有问题，请提交Issue：https://github.com/snrzz/risk/issues
