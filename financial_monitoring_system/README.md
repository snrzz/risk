# 金融风控监控系统

## 项目简介

金融风控监控系统是一个统一监控平台，用于集中监控O32投资交易系统、估值核算系统、风险控制系统、非标系统、关联交易系统、TA系统、COP系统等金融业务系统。

## 主要功能

- **统一监控**: 集中监控多个业务系统的关键指标
- **告警管理**: 灵活的告警规则配置，支持多渠道实时通知
- **数据分析**: 指标趋势分析、异常检测、风险评估
- **报告生成**: 自动生成日报、周报、月报
- **可视化**: 实时仪表盘、图表展示

## 快速开始

### 环境要求
- Docker >= 20.10
- Docker Compose >= 2.0
- 内存 >= 4GB
- 磁盘 >= 20GB

### 部署步骤

```bash
# 1. 进入项目目录
cd financial_monitoring_system

# 2. 配置参数
vim config/settings.yaml

# 3. 初始化数据库
python scripts/init_db.py init
python scripts/init_db.py seed

# 4. 启动服务
docker-compose up -d

# 5. 访问系统
# 前端: http://localhost:8080
# API文档: http://localhost:8000/docs
```

## 项目结构

```
financial_monitoring_system/
├── docker-compose.yml          # Docker编排配置
├── config/
│   ├── settings.yaml          # 应用配置
│   └── nginx.conf             # Nginx配置
├── src/
│   ├── backend/               # 后端项目 (Python + FastAPI)
│   └── frontend/              # 前端项目 (Vue3 + Element Plus)
├── scripts/
│   └── init_db.py             # 数据库初始化脚本
├── docs/
│   ├── 架构设计.md            # 系统架构设计文档
│   ├── 数据库设计.sql         # 数据库表结构
│   └── 部署手册.md            # 部署实施指南
└── README.md
```

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue3 + Element Plus + ECharts |
| 后端 | Python + FastAPI |
| 数据库 | SQLite (开发) / MySQL (生产) |
| 定时任务 | APScheduler |
| 部署 | Docker Compose |

## 监控范围

### 支持的业务系统
- O32投资交易系统
- 估值核算系统
- 风险控制系统
- 非标系统
- 关联交易系统
- TA系统
- COP系统

### 监控指标类型
- 交易监控: 持仓、成交、资金
- 估值监控: 净值、资产价值
- 风险监控: VaR、集中度、杠杆
- 运营监控: 处理时效、完整率

## 配置说明

### 数据源配置
系统支持多种数据接入方式:
- 数据库视图
- CSV/Excel/JSON文件
- 日志文件

### 告警规则
支持多种条件类型:
- 阈值告警 (>)
- 范围告警 (区间)
- 变化率告警 (%)
- 趋势告警 (连续N次)

### 通知渠道
支持多渠道告警:
- 飞书
- 企业微信
- 邮件
- 钉钉
- Telegram
- Webhook

## 文档

- [架构设计](docs/架构设计.md) - 系统架构详解
- [数据库设计](docs/数据库设计.sql) - 数据库表结构
- [部署手册](docs/部署手册.md) - 完整部署指南

## License

MIT License
