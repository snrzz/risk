# API文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/`
- **认证**: JWT Token (Bearer Token)
- **响应格式**: JSON

## 认证接口

### 登录
```
POST /api/token/
Content-Type: application/json

Request:
{
    "email": "admin@example.com",
    "password": "admin123"
}

Response:
{
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 1,
        "email": "admin@example.com",
        "phone": null,
        "department": null,
        "is_active": true,
        "roles": [...]
    }
}
```

### 刷新Token
```
POST /api/token/refresh/
Content-Type: application/json

Request:
{
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
}

Response:
{
    "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 登出
```
POST /api/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
}

Response:
{
    "message": "登出成功"
}
```

## 用户管理

### 获取当前用户
```
GET /api/accounts/users/me/
Authorization: Bearer <access_token>

Response:
{
    "id": 1,
    "email": "admin@example.com",
    "phone": "13800138000",
    "department": "投资部",
    "position": "投资经理",
    "is_active": true,
    "roles": [...]
}
```

### 用户列表
```
GET /api/accounts/users/
Authorization: Bearer <access_token>
Query Params:
    - is_active: true/false
    - department: 部门名称
    - search: 搜索关键词

Response:
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [...]
}
```

### 创建用户
```
POST /api/accounts/users/
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
    "email": "newuser@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "phone": "13900139000",
    "department": "风控部",
    "position": "风控经理",
    "role_ids": [1, 2]
}
```

### 修改密码
```
POST /api/accounts/users/{id}/change_password/
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
    "old_password": "oldpassword",
    "new_password": "newpassword"
}

Response:
{
    "message": "密码修改成功"
}
```

## 组合管理

### 组合列表
```
GET /api/risk/portfolios/
Authorization: Bearer <access_token>
Query Params:
    - status: active/suspended/closed
    - type: stock/bond/mixed/index
    - search: 搜索关键词

Response:
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "code": "P001",
            "name": "测试组合",
            "manager": "张经理",
            "portfolio_type": "mixed",
            "status": "active",
            "asset_scale": 10000000.00,
            "created_at": "2025-01-17T10:00:00Z",
            "updated_at": "2025-01-17T10:00:00Z"
        }
    ]
}
```

### 获取组合详情
```
GET /api/risk/portfolios/{id}/
Authorization: Bearer <access_token>

Response:
{
    "id": 1,
    "code": "P001",
    "name": "测试组合",
    ...
}
```

### 获取组合风险汇总
```
GET /api/risk/portfolios/{id}/risk_summary/
Authorization: Bearer <access_token>

Response:
{
    "portfolio": {...},
    "latest_indicator": {...},
    "today_trades": {
        "count": 10,
        "amount": 500000.00
    },
    "pending_alerts": 3
}
```

## 风险指标

### 获取最新风险指标
```
GET /api/risk/indicators/latest/
Authorization: Bearer <access_token>

Response:
[
    {
        "id": 1,
        "portfolio": {
            "id": 1,
            "code": "P001",
            "name": "测试组合"
        },
        "indicator_date": "2025-01-17",
        "daily_return": 0.0012,
        "cumulative_return": 0.0523,
        "annualized_return": 0.1234,
        "sharpe_ratio": 0.6523,
        "max_drawdown": -0.0523,
        "value_at_risk": 0.0234,
        ...
    }
]
```

### 获取组合历史指标
```
GET /api/risk/indicators/history/
Authorization: Bearer <access_token>
Query Params:
    - portfolio: 组合ID
    - start_date: 开始日期 (2025-01-01)
    - end_date: 结束日期 (2025-01-17)

Response:
[
    {
        "indicator_date": "2025-01-01",
        "daily_return": 0.0023,
        "sharpe_ratio": 0.6523,
        ...
    },
    ...
]
```

## 交易监控

### 交易列表
```
GET /api/risk/trades/
Authorization: Bearer <access_token>
Query Params:
    - portfolio: 组合ID
    - type: buy/sell
    - status: pending/filled/cancelled
    - start_date: 开始日期
    - end_date: 结束日期
    - is_abnormal: true/false
    - search: 搜索关键词

Response:
{
    "count": 100,
    "results": [...]
}
```

### 交易统计
```
GET /api/risk/trades/summary/
Authorization: Bearer <access_token>
Query Params:
    - portfolio: 组合ID
    - start_date: 开始日期
    - end_date: 结束日期

Response:
{
    "total_count": 100,
    "total_amount": 50000000.00,
    "buy_count": 60,
    "sell_count": 40,
    "abnormal_count": 3
}
```

### 异常交易
```
GET /api/risk/trades/abnormal/
Authorization: Bearer <access_token>

Response:
{
    "count": 3,
    "results": [...]
}
```

## 风险预警

### 预警列表
```
GET /api/risk/alerts/
Authorization: Bearer <access_token>
Query Params:
    - status: pending/acknowledged/resolved/ignored
    - severity: info/warning/error/critical
    - type: threshold/anomaly/limit/trend
    - portfolio: 组合ID
    - start_date: 开始日期
    - end_date: 结束日期

Response:
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "alert_type": "threshold",
            "severity": "warning",
            "title": "最大回撤预警",
            "content": "组合P001最大回撤超过阈值",
            "portfolio": {"id": 1, "code": "P001"},
            "status": "pending",
            "alert_time": "2025-01-17T10:00:00Z"
        }
    ]
}
```

### 待处理预警
```
GET /api/risk/alerts/pending/
Authorization: Bearer <access_token>

Response:
{
    "count": 5,
    "results": [...]
}
```

### 预警统计
```
GET /api/risk/alerts/statistics/
Authorization: Bearer <access_token>

Response:
{
    "by_status": [
        {"status": "pending", "count": 5},
        {"status": "resolved", "count": 10}
    ],
    "by_severity": [
        {"severity": "warning", "count": 3},
        {"severity": "critical", "count": 2}
    ],
    "by_type": [
        {"alert_type": "threshold", "count": 8}
    ]
}
```

### 更新预警状态
```
PATCH /api/risk/alerts/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
    "status": "resolved",
    "handle_comment": "已处理"
}

Response:
{
    "id": 1,
    "status": "resolved",
    "handled_at": "2025-01-17T10:30:00Z",
    "handle_comment": "已处理"
}
```

## 仪表盘

### 风险仪表盘
```
GET /api/risk/dashboard/
Authorization: Bearer <access_token>

Response:
{
    "total_portfolios": 10,
    "active_portfolios": 8,
    "today_trades": 15,
    "today_amount": 5000000.00,
    "pending_alerts": 3,
    "critical_alerts": 1,
    "total_return": 0.0523,
    "avg_sharpe_ratio": 0.85
}
```

## 定时任务

### 任务列表
```
GET /api/tasks/
Authorization: Bearer <access_token>

Response:
[
    {
        "name": "sync_risk_indicators",
        "description": "同步风险指标数据",
        "schedule": "每天 6:00",
        "enabled": true
    },
    ...
]
```

### 手动执行任务
```
POST /api/tasks/execute/
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
    "task_name": "sync_risk_indicators"
}

Response:
{
    "message": "任务sync_risk_indicators已开始执行",
    "task_id": "abc123"
}
```

### 任务状态
```
GET /api/tasks/status/
Authorization: Bearer <access_token>
Query Params:
    - task_id: 任务ID

Response:
{
    "task_id": "abc123",
    "status": "SUCCESS",
    "result": {...}
}
```

## 错误响应

### 错误格式
```json
{
    "error": "错误描述信息"
}
```

### 常见错误码

| 状态码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或Token过期 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 限流规则

- 匿名用户: 100次/天
- 登录用户: 1000次/天
