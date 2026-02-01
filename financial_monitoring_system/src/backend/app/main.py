"""
金融风控监控系统 - 后端主程序入口
"""
import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import engine, Base
from app.routers import (
    dashboard,
    metrics,
    alerts,
    data_sources,
    rules,
    reports,
    notify,
    admin,
)
from app.schedulers import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("🚀 启动金融风控监控系统...")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库表创建完成")
    
    # 启动定时任务调度器
    start_scheduler()
    logger.info("✅ 定时任务调度器已启动")
    
    yield
    
    # 关闭时
    logger.info("🛑 正在关闭系统...")
    stop_scheduler()
    logger.info("✅ 定时任务调度器已停止")
    logger.info("👋 系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="金融风控监控系统",
    description="统一监控O32、估值、风控、非标、关联交易、TA、COP等业务系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["仪表盘"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["指标管理"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["告警管理"])
app.include_router(data_sources.router, prefix="/api/v1/datasources", tags=["数据源管理"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["规则管理"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["报告管理"])
app.include_router(notify.router, prefix="/api/v1/notify", tags=["通知渠道"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["系统管理"])


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": asyncio.datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "金融风控监控系统",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    )
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
