"""
系统管理路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.models import SystemConfig, SystemLog, DataSource, MetricDefinition
from app.schemas import BaseResponse


router = APIRouter()


@router.get("/config")
async def get_system_config(db: AsyncSession = Depends(get_db)):
    """获取系统配置"""
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    config_dict = {c.key: c.value for c in configs}
    return {"config": config_dict}


@router.put("/config")
async def update_system_config(
    key: str,
    value: str,
    description: str = None,
    db: AsyncSession = Depends(get_db)
):
    """更新系统配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = value
        if description:
            config.description = description
    else:
        config = SystemConfig(
            key=key,
            value=value,
            description=description
        )
        db.add(config)
    
    await db.commit()
    
    return {"message": "配置已更新"}


@router.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """获取系统统计"""
    # 数据源统计
    total_sources = await db.scalar(select(func.count(DataSource.id)))
    active_sources = await db.scalar(
        select(func.count(DataSource.id)).where(DataSource.status == "active")
    )
    
    # 指标统计
    total_metrics = await db.scalar(select(func.count(MetricDefinition.id)))
    
    # 最近日志
    result = await db.execute(
        select(SystemLog)
        .order_by(SystemLog.log_time.desc())
        .limit(10)
    )
    recent_logs = result.scalars().all()
    
    return {
        "datasources": {
            "total": total_sources or 0,
            "active": active_sources or 0
        },
        "metrics": {
            "total": total_metrics or 0
        },
        "recent_logs": [
            {
                "time": log.log_time.isoformat(),
                "level": log.level,
                "message": log.message
            }
            for log in recent_logs
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/logs")
async def get_system_logs(
    level: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100
):
    """获取系统日志"""
    # TODO: 实现日志查询
    return {"logs": []}


@router.post("/db/init")
async def initialize_database(db: AsyncSession = Depends(get_db)):
    """初始化数据库"""
    try:
        init_db()
        return {"message": "数据库初始化完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库初始化失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    return {
        "name": "金融风控监控系统",
        "version": "1.0.0",
        "description": "统一监控O32、估值、风控、非标、关联交易、TA、COP等业务系统",
        "features": [
            "多数据源支持（数据库视图、CSV、Excel、JSON等）",
            "灵活的告警规则配置",
            "多渠道通知（飞书、企业微信、邮件、钉钉等）",
            "实时仪表盘",
            "自动报告生成"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
