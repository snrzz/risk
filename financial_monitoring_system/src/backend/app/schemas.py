"""
Pydantic Schemas - 请求/响应模型
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ============================================================
# 基础模型
# ============================================================

class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================
# 数据源
# ============================================================

class DataSourceCreate(BaseModel):
    """数据源创建请求"""
    name: str
    code: str
    source_type: str
    connection_info: Dict[str, Any]
    config_schema: Optional[Dict[str, Any]] = None
    sync_interval: int = 300


class DataSourceUpdate(BaseModel):
    """数据源更新请求"""
    name: Optional[str] = None
    source_type: Optional[str] = None
    connection_info: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    sync_interval: Optional[int] = None


class DataSourceResponse(BaseModel):
    """数据源响应"""
    id: int
    name: str
    code: str
    source_type: str
    status: str
    last_sync_time: Optional[datetime]
    sync_interval: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# 指标定义
# ============================================================

class MetricCreate(BaseModel):
    """指标创建请求"""
    code: str
    name: str
    description: Optional[str] = None
    category: str
    data_source_id: Optional[int] = None
    field_name: str
    field_type: str = "number"
    unit: Optional[str] = None
    aggregation_type: Optional[str] = None
    expression: Optional[str] = None


class MetricUpdate(BaseModel):
    """指标更新请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    field_name: Optional[str] = None
    field_type: Optional[str] = None
    unit: Optional[str] = None
    aggregation_type: Optional[str] = None
    expression: Optional[str] = None


class MetricResponse(BaseModel):
    """指标响应"""
    id: int
    code: str
    name: str
    description: Optional[str]
    category: Optional[str]
    data_source_id: Optional[int]
    field_name: Optional[str]
    field_type: str
    unit: Optional[str]
    aggregation_type: Optional[str]
    expression: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# 指标数据
# ============================================================

class MetricDataQuery(BaseModel):
    """指标数据查询"""
    metric_codes: List[str]
    start_time: datetime
    end_time: datetime
    aggregation: Optional[str] = None  # hour, day, week, month


class MetricDataPoint(BaseModel):
    """指标数据点"""
    metric_code: str
    timestamp: datetime
    value: float


class MetricDataResponse(BaseModel):
    """指标数据响应"""
    metric_code: str
    data: List[MetricDataPoint]


# ============================================================
# 告警规则
# ============================================================

class AlertRuleCreate(BaseModel):
    """告警规则创建请求"""
    code: str
    name: str
    description: Optional[str] = None
    metric_code: str
    condition_type: str
    condition_config: Dict[str, Any]
    severity: str
    notify_channels: List[str]
    notify_users: Optional[List[str]] = None
    cooldown_minutes: int = 10


class AlertRuleUpdate(BaseModel):
    """告警规则更新请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    condition_type: Optional[str] = None
    condition_config: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    notify_channels: Optional[List[str]] = None
    notify_users: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    """告警规则响应"""
    id: int
    code: str
    name: str
    description: Optional[str]
    metric_code: str
    condition_type: str
    condition_config: Dict[str, Any]
    severity: str
    status: str
    notify_channels: List[str]
    notify_users: Optional[List[str]]
    cooldown_minutes: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# 告警记录
# ============================================================

class AlertRecordResponse(BaseModel):
    """告警记录响应"""
    id: int
    rule_code: str
    metric_code: str
    alert_time: datetime
    alert_value: float
    threshold_value: Optional[float]
    severity: str
    message: Optional[str]
    status: str
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolved_message: Optional[str]
    notification_sent: bool
    notification_channels: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertAckRequest(BaseModel):
    """告警确认请求"""
    record_ids: List[int]
    acknowledged_by: str
    message: Optional[str] = None


class AlertResolveRequest(BaseModel):
    """告警解决请求"""
    record_ids: List[int]
    resolved_by: str
    message: str


class AlertStats(BaseModel):
    """告警统计"""
    total: int
    active: int
    acknowledged: int
    resolved: int
    by_severity: Dict[str, int]


# ============================================================
# 仪表盘
# ============================================================

class DashboardSummary(BaseModel):
    """仪表盘摘要"""
    total_metrics: int
    active_rules: int
    alerts_today: int
    critical_alerts: int
    system_status: str


class DashboardChart(BaseModel):
    """仪表盘图表数据"""
    name: str
    type: str  # line, bar, pie, area
    categories: List[str]
    series: List[Dict[str, Any]]


class DashboardResponse(BaseModel):
    """仪表盘响应"""
    summary: DashboardSummary
    recent_alerts: List[AlertRecordResponse]
    charts: List[DashboardChart]
    top_metrics: List[Dict[str, Any]]


# ============================================================
# 通知渠道
# ============================================================

class NotifyChannelCreate(BaseModel):
    """通知渠道创建请求"""
    code: str
    name: str
    channel_type: str
    config: Dict[str, Any]


class NotifyChannelUpdate(BaseModel):
    """通知渠道更新请求"""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class NotifyChannelResponse(BaseModel):
    """通知渠道响应"""
    id: int
    code: str
    name: str
    channel_type: str
    config: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# 报告
# ============================================================

class ReportTemplateCreate(BaseModel):
    """报告模板创建请求"""
    code: str
    name: str
    report_type: str
    content_template: str
    schedule_cron: Optional[str] = None
    recipients: Optional[List[str]] = None
    notify_channels: Optional[List[str]] = None


class ReportTemplateUpdate(BaseModel):
    """报告模板更新请求"""
    name: Optional[str] = None
    content_template: Optional[str] = None
    schedule_cron: Optional[str] = None
    recipients: Optional[List[str]] = None
    notify_channels: Optional[List[str]] = None
    status: Optional[str] = None


class ReportTemplateResponse(BaseModel):
    """报告模板响应"""
    id: int
    code: str
    name: str
    report_type: str
    content_template: str
    schedule_cron: Optional[str]
    recipients: Optional[List[str]]
    notify_channels: Optional[List[str]]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    """报告生成请求"""
    template_id: int
    time_range_start: datetime
    time_range_end: datetime
    recipients: Optional[List[str]] = None


class ReportRecordResponse(BaseModel):
    """报告记录响应"""
    id: int
    template_id: int
    template_code: str
    report_time: datetime
    time_range_start: Optional[datetime]
    time_range_end: Optional[datetime]
    content: Optional[str]
    file_path: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
