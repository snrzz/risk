-- ============================================================
-- 金融风控监控系统 - 数据库表结构设计
-- 支持: SQLite (开发), MySQL (生产)
-- ============================================================

-- ============================================================
-- 1. 系统配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,      -- 配置键
    value TEXT,                             -- 配置值
    description VARCHAR(255),               -- 配置说明
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化默认配置
INSERT INTO system_config (key, value, description) VALUES
('system_name', '金融风控监控系统', '系统名称'),
('check_interval', '300', '数据采集间隔(秒)'),
('alert_check_interval', '60', '告警检查间隔(秒)'),
('data_retention_days', '90', '历史数据保留天数'),
('timezone', 'Asia/Shanghai', '时区设置');

-- ============================================================
-- 2. 数据源配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS data_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,             -- 数据源名称 (如: O32投资交易系统)
    code VARCHAR(50) UNIQUE NOT NULL,       -- 数据源编码 (如: o32_trading)
    source_type VARCHAR(20) NOT NULL,       -- 类型: database_view, csv_file, excel_file, json_file
    connection_info TEXT,                   -- 连接信息 (JSON格式, 包含数据库连接串/文件路径等)
    config_schema TEXT,                     -- 配置Schema (JSON格式, 定义字段映射)
    status VARCHAR(10) DEFAULT 'active',    -- 状态: active, inactive, error
    last_sync_time DATETIME,                -- 最后同步时间
    sync_interval INTEGER DEFAULT 300,      -- 同步间隔(秒)
    error_message TEXT,                     -- 错误信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_data_source_code ON data_source(code);
CREATE INDEX idx_data_source_status ON data_source(status);

-- ============================================================
-- 3. 监控指标定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS metric_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 指标编码
    name VARCHAR(100) NOT NULL,             -- 指标名称
    description TEXT,                       -- 指标说明
    category VARCHAR(50),                   -- 分类: trading, valuation, risk, non_standard, related_party, ta, cop
    data_source_id INTEGER,                 -- 关联数据源
    field_name VARCHAR(100),                -- 字段名 (从数据源中取值的字段)
    field_type VARCHAR(20) DEFAULT 'number',-- 字段类型: number, string, datetime
    unit VARCHAR(20),                       -- 单位: %, 元, 股, etc.
    aggregation_type VARCHAR(20),           -- 聚合方式: sum, avg, max, min, last, count
    expression TEXT,                        -- 计算表达式 (如: {field_a} / {field_b} * 100)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_source_id) REFERENCES data_source(id)
);

-- 索引
CREATE INDEX idx_metric_category ON metric_definition(category);
CREATE INDEX idx_metric_datasource ON metric_definition(data_source_id);

-- ============================================================
-- 4. 监控指标历史数据表 (时序数据)
-- ============================================================
CREATE TABLE IF NOT EXISTS metric_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_code VARCHAR(50) NOT NULL,       -- 指标编码
    data_time DATETIME NOT NULL,            -- 数据时间点
    value DOUBLE NOT NULL,                  -- 指标值
    raw_data TEXT,                          -- 原始数据 (JSON)
    status VARCHAR(10) DEFAULT 'normal',    -- 数据状态: normal, abnormal, missing
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_code) REFERENCES metric_definition(code)
);

-- 索引 (时序数据关键索引)
CREATE INDEX idx_metric_data_metric_time ON metric_data(metric_code, data_time DESC);
CREATE INDEX idx_metric_data_time ON metric_data(data_time DESC);

-- ============================================================
-- 5. 告警规则定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS alert_rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 规则编码
    name VARCHAR(100) NOT NULL,             -- 规则名称
    description TEXT,                       -- 规则说明
    metric_code VARCHAR(50) NOT NULL,       -- 关联指标
    condition_type VARCHAR(20) NOT NULL,    -- 条件类型: threshold, range, trend, change_rate, combine
    condition_config TEXT NOT NULL,         -- 条件配置 (JSON)
    severity VARCHAR(10) NOT NULL,          -- 级别: P1, P2, P3, P4
    status VARCHAR(10) DEFAULT 'active',    -- 状态: active, inactive
    notify_channels TEXT,                   -- 通知渠道 (JSON: ["lark", "email"])
    notify_users TEXT,                      -- 通知用户 (JSON: ["user1", "user2"])
    cooldown_minutes INTEGER DEFAULT 10,    -- 冷却时间(分钟)
    enabled INTEGER DEFAULT 1,              -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_code) REFERENCES metric_definition(code)
);

-- 索引
CREATE INDEX idx_alert_rule_metric ON alert_rule(metric_code);
CREATE INDEX idx_alert_rule_status ON alert_rule(status);
CREATE INDEX idx_alert_rule_severity ON alert_rule(severity);

-- ============================================================
-- 6. 告警记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS alert_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,               -- 告警规则ID
    rule_code VARCHAR(50) NOT NULL,         -- 规则编码
    metric_code VARCHAR(50) NOT NULL,       -- 指标编码
    alert_time DATETIME NOT NULL,           -- 告警时间
    alert_value DOUBLE NOT NULL,            -- 触发值
    threshold_value DOUBLE,                 -- 阈值
    severity VARCHAR(10) NOT NULL,          -- 级别
    message TEXT,                           -- 告警消息
    status VARCHAR(10) DEFAULT 'active',    -- 状态: active, acknowledged, resolved, expired
    acknowledged_by VARCHAR(50),            -- 确认人
    acknowledged_at DATETIME,               -- 确认时间
    resolved_by VARCHAR(50),                -- 解决人
    resolved_at DATETIME,                   -- 解决时间
    resolved_message TEXT,                  -- 解决说明
    notification_sent INTEGER DEFAULT 0,    -- 是否已发送通知
    notification_channels TEXT,             -- 已发送渠道
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES alert_rule(id)
);

-- 索引
CREATE INDEX idx_alert_record_time ON alert_record(alert_time DESC);
CREATE INDEX idx_alert_record_status ON alert_record(status);
CREATE INDEX idx_alert_record_metric ON alert_record(metric_code);
CREATE INDEX idx_alert_record_severity ON alert_record(severity);

-- ============================================================
-- 7. 通知渠道配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS notify_channel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 渠道编码
    name VARCHAR(100) NOT NULL,             -- 渠道名称
    channel_type VARCHAR(20) NOT NULL,      -- 类型: lark, wecom, email, dingtalk, telegram, webhook
    config TEXT NOT NULL,                   -- 配置信息 (JSON)
    status VARCHAR(10) DEFAULT 'active',    -- 状态
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 8. 用户配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,   -- 用户名
    display_name VARCHAR(100),              -- 显示名称
    email VARCHAR(100),                     -- 邮箱
    phone VARCHAR(20),                      -- 手机
    lark_user_id VARCHAR(50),               -- 飞书用户ID
    wecom_user_id VARCHAR(50),              -- 企业微信用户ID
    roles TEXT,                             -- 角色 (JSON: ["admin", "viewer"])
    notify_preferences TEXT,                -- 通知偏好 (JSON)
    status VARCHAR(10) DEFAULT 'active',    -- 状态
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化管理员用户
INSERT INTO user_profile (username, display_name, roles) VALUES
('admin', '系统管理员', '["admin"]');

-- ============================================================
-- 9. 报告模板表
-- ============================================================
CREATE TABLE IF NOT EXISTS report_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 模板编码
    name VARCHAR(100) NOT NULL,             -- 模板名称
    report_type VARCHAR(20) NOT NULL,       -- 类型: daily, weekly, monthly, custom
    content_template TEXT NOT NULL,         -- 内容模板 (Jinja2)
    schedule_cron VARCHAR(50),              -- 调度CRON表达式
    recipients TEXT,                        -- 收件人 (JSON)
    notify_channels TEXT,                   -- 发送渠道
    status VARCHAR(10) DEFAULT 'active',    -- 状态
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 10. 报告记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS report_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,           -- 模板ID
    template_code VARCHAR(50) NOT NULL,     -- 模板编码
    report_time DATETIME NOT NULL,          -- 报告时间
    time_range_start DATETIME,              -- 数据时间范围-开始
    time_range_end DATETIME,                -- 数据时间范围-结束
    content TEXT,                           -- 报告内容 (HTML/Markdown)
    file_path VARCHAR(255),                 -- 导出文件路径
    status VARCHAR(10) DEFAULT 'generated', -- 状态: generating, generated, failed
    error_message TEXT,                     -- 错误信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);

-- 索引
CREATE INDEX idx_report_record_time ON report_record(report_time DESC);
CREATE INDEX idx_report_record_template ON report_record(template_id);

-- ============================================================
-- 11. 系统日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS system_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_time DATETIME NOT NULL,             -- 日志时间
    level VARCHAR(10) NOT NULL,             -- 级别: DEBUG, INFO, WARNING, ERROR
    module VARCHAR(50),                     -- 模块
    message TEXT NOT NULL,                  -- 日志消息
    extra_data TEXT,                        -- 额外数据 (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_system_log_time ON system_log(log_time DESC);
CREATE INDEX idx_system_log_level ON system_log(level);

-- ============================================================
-- 12. 数据同步日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source_id INTEGER NOT NULL,        -- 数据源ID
    sync_type VARCHAR(20) NOT NULL,         -- 同步类型: full, incremental
    start_time DATETIME NOT NULL,           -- 开始时间
    end_time DATETIME,                      -- 结束时间
    records_processed INTEGER DEFAULT 0,    -- 处理记录数
    status VARCHAR(10) DEFAULT 'running',   -- 状态: running, success, failed
    error_message TEXT,                     -- 错误信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_source_id) REFERENCES data_source(id)
);

-- 索引
CREATE INDEX idx_sync_log_source ON sync_log(data_source_id);
CREATE INDEX idx_sync_log_time ON sync_log(start_time DESC);

-- ============================================================
-- 触发器: 更新时间戳
-- ============================================================
CREATE TRIGGER IF NOT EXISTS update_timestamp 
AFTER UPDATE ON system_config
BEGIN
    UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_timestamp_datasource 
AFTER UPDATE ON data_source
BEGIN
    UPDATE data_source SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_timestamp_alertrule 
AFTER UPDATE ON alert_rule
BEGIN
    UPDATE alert_rule SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_timestamp_reporttemplate 
AFTER UPDATE ON report_template
BEGIN
    UPDATE report_template SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_timestamp_userprofile 
AFTER UPDATE ON user_profile
BEGIN
    UPDATE user_profile SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_timestamp_notifychannel 
AFTER UPDATE ON notify_channel
BEGIN
    UPDATE notify_channel SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
