"""
数据模型定义 - SQLAlchemy ORM
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataSource(Base):
    """数据源配置表"""
    __tablename__ = "data_source"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    source_type = Column(String(20), nullable=False)  # database_view, csv_file, excel_file, json_file
    connection_info = Column(JSON)  # 连接信息
    config_schema = Column(JSON)  # 配置Schema
    status = Column(String(10), default='active')  # active, inactive, error
    last_sync_time = Column(DateTime)
    sync_interval = Column(Integer, default=300)  # 秒
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    metrics = relationship("MetricDefinition", back_populates="data_source")
    sync_logs = relationship("SyncLog", back_populates="data_source")


class MetricDefinition(Base):
    """监控指标定义表"""
    __tablename__ = "metric_definition"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # trading, valuation, risk, non_standard, related_party, ta, cop
    data_source_id = Column(Integer, ForeignKey("data_source.id"))
    field_name = Column(String(100))  # 字段名
    field_type = Column(String(20), default='number')  # number, string, datetime
    unit = Column(String(20))  # 单位
    aggregation_type = Column(String(20))  # sum, avg, max, min, last, count
    expression = Column(Text)  # 计算表达式
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    data_source = relationship("DataSource", back_populates="metrics")
    alert_rules = relationship("AlertRule", back_populates="metric")
    metric_data = relationship("MetricData", back_populates="metric")


class MetricData(Base):
    """监控指标历史数据表 (时序数据)"""
    __tablename__ = "metric_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_code = Column(String(50), ForeignKey("metric_definition.code"), nullable=False)
    data_time = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    raw_data = Column(JSON)  # 原始数据
    status = Column(String(10), default='normal')  # normal, abnormal, missing
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    metric = relationship("MetricDefinition", back_populates="metric_data")
    
    # 索引
    __table_args__ = (
        Index("idx_metric_data_metric_time", "metric_code", "data_time"),
        Index("idx_metric_data_time", "data_time"),
    )


class AlertRule(Base):
    """告警规则定义表"""
    __tablename__ = "alert_rule"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    metric_code = Column(String(50), ForeignKey("metric_definition.code"), nullable=False)
    condition_type = Column(String(20), nullable=False)  # threshold, range, trend, change_rate, combine
    condition_config = Column(JSON, nullable=False)  # 条件配置
    severity = Column(String(10), nullable=False)  # P1, P2, P3, P4
    status = Column(String(10), default='active')  # active, inactive
    notify_channels = Column(JSON)  # 通知渠道
    notify_users = Column(JSON)  # 通知用户
    cooldown_minutes = Column(Integer, default=10)  # 冷却时间
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    metric = relationship("MetricDefinition", back_populates="alert_rules")
    alert_records = relationship("AlertRecord", back_populates="rule")


class AlertRecord(Base):
    """告警记录表"""
    __tablename__ = "alert_record"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("alert_rule.id"), nullable=False)
    rule_code = Column(String(50), nullable=False)
    metric_code = Column(String(50), nullable=False)
    alert_time = Column(DateTime, nullable=False)
    alert_value = Column(Float, nullable=False)
    threshold_value = Column(Float)
    severity = Column(String(10), nullable=False)
    message = Column(Text)
    status = Column(String(10), default='active')  # active, acknowledged, resolved, expired
    acknowledged_by = Column(String(50))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime)
    resolved_message = Column(Text)
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    rule = relationship("AlertRule", back_populates="alert_records")
    
    # 索引
    __table_args__ = (
        Index("idx_alert_record_time", "alert_time"),
        Index("idx_alert_record_status", "status"),
        Index("idx_alert_record_metric", "metric_code"),
    )


class NotifyChannel(Base):
    """通知渠道配置表"""
    __tablename__ = "notify_channel"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    channel_type = Column(String(20), nullable=False)  # lark, wecom, email, dingtalk, telegram, webhook
    config = Column(JSON, nullable=False)  # 配置信息
    status = Column(String(10), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    """用户配置表"""
    __tablename__ = "user_profile"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    lark_user_id = Column(String(50))
    wecom_user_id = Column(String(50))
    roles = Column(JSON)  # 角色列表
    notify_preferences = Column(JSON)  # 通知偏好
    status = Column(String(10), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportTemplate(Base):
    """报告模板表"""
    __tablename__ = "report_template"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    report_type = Column(String(20), nullable=False)  # daily, weekly, monthly, custom
    content_template = Column(Text, nullable=False)  # Jinja2模板
    schedule_cron = Column(String(50))  # CRON表达式
    recipients = Column(JSON)  # 收件人
    notify_channels = Column(JSON)  # 发送渠道
    status = Column(String(10), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportRecord(Base):
    """报告记录表"""
    __tablename__ = "report_record"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("report_template.id"), nullable=False)
    template_code = Column(String(50), nullable=False)
    report_time = Column(DateTime, nullable=False)
    time_range_start = Column(DateTime)
    time_range_end = Column(DateTime)
    content = Column(Text)  # 报告内容
    file_path = Column(String(255))  # 导出文件路径
    status = Column(String(10), default='generated')  # generating, generated, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index("idx_report_record_time", "report_time"),
    )


class SyncLog(Base):
    """数据同步日志表"""
    __tablename__ = "sync_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_source_id = Column(Integer, ForeignKey("data_source.id"), nullable=False)
    sync_type = Column(String(20), nullable=False)  # full, incremental
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    records_processed = Column(Integer, default=0)
    status = Column(String(10), default='running')  # running, success, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    data_source = relationship("DataSource", back_populates="sync_logs")
    
    # 索引
    __table_args__ = (
        Index("idx_sync_log_source", "data_source_id"),
        Index("idx_sync_log_time", "start_time"),
    )


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_time = Column(DateTime, nullable=False)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    module = Column(String(50))
    message = Column(Text, nullable=False)
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index("idx_system_log_time", "log_time"),
        Index("idx_system_log_level", "level"),
    )
