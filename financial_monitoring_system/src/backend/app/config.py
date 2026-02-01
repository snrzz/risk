"""
系统配置管理
"""
from pathlib import Path
from typing import List, Optional
import os
import json
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from loguru import logger


# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = "sqlite"  # sqlite, mysql
    host: str = "localhost"
    port: int = 3306
    username: str = "root"
    password: str = ""
    name: str = "financial_monitoring.db"
    pool_size: int = 5
    max_overflow: int = 10
    
    @property
    def url(self) -> str:
        if self.type == "sqlite":
            db_path = CONFIG_DIR / "data" / self.name
            return f"sqlite+aiosqlite:///{db_path}"
        return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{port}/{self.name}"


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "金融风控监控系统"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-change-in-production"
    cors_origins: List[str] = ["*"]


class SchedulerConfig(BaseModel):
    """调度器配置"""
    check_interval: int = 60  # 告警检查间隔(秒)
    data_sync_interval: int = 300  # 数据同步间隔(秒)
    report_generate_time: str = "07:00"  # 报告生成时间
    timezone: str = "Asia/Shanghai"


class NotifyConfig(BaseModel):
    """通知配置"""
    default_channels: List[str] = ["lark"]
    max_retry_times: int = 3
    retry_interval: int = 60


class Settings(BaseSettings):
    """全局设置"""
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: Optional[RedisConfig] = None
    scheduler: SchedulerConfig = SchedulerConfig()
    notify: NotifyConfig = NotifyConfig()
    
    class Config:
        env_prefix = "FM_"
        env_nested_delimiter = "__"


def load_config(config_file: Path = SETTINGS_FILE) -> Settings:
    """加载配置文件"""
    if not config_file.exists():
        logger.warning(f"配置文件不存在: {config_file}")
        return Settings()
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
        
        return Settings(**config_data)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return Settings()


# 全局设置实例
settings = load_config()

# 导出常用配置
APP_NAME = settings.app.name
HOST = settings.app.host
PORT = settings.app.port
DEBUG = settings.app.debug
LOG_LEVEL = settings.app.log_level
CORS_ORIGINS = settings.app.cors_origins

DATABASE_URL = settings.database.url
DATABASE_TYPE = settings.database.type

SCHEDULER_CHECK_INTERVAL = settings.scheduler.check_interval
SCHEDULER_SYNC_INTERVAL = settings.scheduler.data_sync_interval

NOTIFY_MAX_RETRY = settings.notify.max_retry_times
NOTIFY_RETRY_INTERVAL = settings.notify.retry_interval
