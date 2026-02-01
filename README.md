# 保险资产管理风险预警系统

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-green.svg)
![Django](https://img.shields.io/badge/Django-4.2+-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)

一个专为保险资产管理公司设计的风险预警系统，提供组合管理、风险监控、交易监控、预警通知等功能。

## 功能特性

### 核心功能
- **组合管理** - 投资组合的CRUD操作，支持多种组合类型
- **风险指标监控** - 实时跟踪收益率、夏普比率、最大回撤等指标
- **交易监控** - 实时监控交易记录，检测异常交易
- **风险预警** - 多级别预警（信息/警告/错误/严重），支持阈值配置
- **仪表盘** - 综合数据展示，支持图表可视化

### 技术特性
- **用户认证** - JWT认证，支持角色权限管理
- **数据缓存** - Redis缓存热点数据，提升性能
- **定时任务** - Celery支持的数据同步和报表导出
- **RESTful API** - 完整的API文档，易于集成

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (生产环境)
- Redis 7+ (可选)

### 方式一：Docker部署（推荐）

```bash
# 克隆项目
git clone https://github.com/snrzz/risk.git
cd risk

# 启动所有服务
docker-compose up -d

# 访问
# Web UI: http://localhost:3000
# API: http://localhost:8000
```

### 方式二：一键部署脚本

```bash
# 下载部署脚本
curl -O https://raw.githubusercontent.com/snrzz/risk/main/deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh
```

### 方式三：手动部署

```bash
# 1. 克隆项目
git clone https://github.com/snrzz/risk.git
cd risk

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env
# 编辑 .env 文件

# 5. 初始化数据库
python manage.py migrate
python manage.py createsuperuser

# 6. 安装前端依赖
cd frontend
npm install
npm run build
cd ..

# 7. 启动服务
python manage.py runserver 0.0.0.0:8000
```

## 默认登录

| 字段 | 值 |
|-----|-----|
| 邮箱 | admin@example.com |
| 密码 | admin123 |

## 项目结构

```
risk/
├── backend/                 # Django后端
│   ├── accounts/           # 用户认证模块
│   │   ├── models.py       # 用户、角色、权限模型
│   │   ├── views.py        # 视图函数
│   │   ├── serializers.py  # 序列化器
│   │   ├── urls.py         # 路由配置
│   │   └── permissions.py  # 权限控制
│   ├── risk/               # 风险监控模块
│   │   ├── models.py       # 风险相关模型
│   │   ├── views.py        # API视图
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── tasks/              # 定时任务模块
│   │   ├── tasks.py        # Celery任务
│   │   └── views.py
│   └── risk_project/       # Django项目配置
│       ├── settings.py
│       ├── urls.py
│       └── celery.py
├── frontend/               # React前端
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API服务
│   │   └── stores/        # 状态管理
│   └── package.json
├── docs/                   # 文档
│   ├── API.md             # API文档
│   ├── DEPLOYMENT.md      # 部署文档
│   └── OPENCLAW_ON_FNOS.md # OpenClaw部署手册
├── docker-compose.yml     # Docker配置
├── deploy.sh              # 一键部署脚本
└── requirements.txt       # Python依赖
```

## API文档

启动服务后访问: http://localhost:8000/api/docs/

主要API端点:

| 模块 | 端点 | 说明 |
|-----|------|------|
| 认证 | `/api/token/` | JWT登录/刷新Token |
| 用户 | `/api/accounts/users/` | 用户管理 |
| 组合 | `/api/risk/portfolios/` | 组合CRUD |
| 指标 | `/api/risk/indicators/` | 风险指标 |
| 交易 | `/api/risk/trades/` | 交易记录 |
| 预警 | `/api/risk/alerts/` | 风险预警 |
| 仪表盘 | `/api/risk/dashboard/` | 综合数据 |

## 配置说明

### 环境变量

```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/risk_db

# Redis缓存
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-secret_TOKEN_LIFETIME_MINUTES=60-key
JWT_ACCESS
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# 邮件配置
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=your-email
EMAIL_PASSWORD=your-password
```

### 风险阈值配置

系统支持配置以下风险指标阈值:

| 指标 | 默认阈值 | 说明 |
|-----|---------|------|
| 最大回撤 | -10% | 超过此值触发预警 |
| VaR(95%) | 5% | 日最大损失预期 |
| 夏普比率 | 0.5 | 低于此值预警 |
| 行业集中度 | 30% | 超过此值预警 |
| 个股集中度 | 10% | 超过此值预警 |

## 定时任务

系统内置以下定时任务:

| 任务 | 调度 | 说明 |
|-----|------|------|
| sync_risk_indicators | 每天6:00 | 同步风险指标 |
| check_risk_alerts | 每小时 | 检查风险预警 |
| export_daily_report | 每天18:00 | 导出日报 |
| detect_abnormal_trades | 每日收盘后 | 异常交易检测 |

## 部署文档

详细的部署指南请参考: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

包括:
- Docker部署
- 生产环境配置
- Nginx配置
- SSL证书配置
- 监控和日志
- 备份恢复

## OpenClaw集成

支持与OpenClaw（AI助手）集成，实现:
- 自然语言风险查询
- 智能预警通知
- 对话式数据分析

部署指南: [docs/OPENCLAW_ON_FNOS.md](docs/OPENCLAW_ON_FNOS.md)

## 测试

```bash
# 运行单元测试
pytest tests.py -v

# 运行API测试
python manage.py test
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系

- GitHub: https://github.com/snrzz/risk
- Issues: https://github.com/snrzz/risk/issues

---

<p align="center">
  Made with ❤️ for Risk Management
</p>
