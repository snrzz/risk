"""
仪表盘路由
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    MetricDefinition, AlertRule, AlertRecord, 
    MetricData, DataSource
)
from app.schemas import (
    DashboardResponse, DashboardSummary, 
    DashboardChart, AlertRecordResponse
)


router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """获取仪表盘摘要"""
    # 指标总数
    total_metrics = await db.scalar(select(func.count(MetricDefinition.id)))
    
    # 活跃规则数
    active_rules = await db.scalar(
        select(func.count(AlertRule.id)).where(AlertRule.enabled == True)
    )
    
    # 今日告警数
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_today = await db.scalar(
        select(func.count(AlertRecord.id)).where(AlertRecord.alert_time >= today)
    )
    
    # 严重告警数
    critical_alerts = await db.scalar(
        select(func.count(AlertRecord.id)).where(
            and_(
                AlertRecord.alert_time >= today,
                AlertRecord.severity == "P1"
            )
        )
    )
    
    return DashboardSummary(
        total_metrics=total_metrics or 0,
        active_rules=active_rules or 0,
        alerts_today=alerts_today or 0,
        critical_alerts=critical_alerts or 0,
        system_status="healthy"
    )


@router.get("/alerts/recent", response_model=List[AlertRecordResponse])
async def get_recent_alerts(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取最近告警"""
    result = await db.execute(
        select(AlertRecord)
        .order_by(AlertRecord.alert_time.desc())
        .limit(limit)
    )
    alerts = result.scalars().all()
    return [AlertRecordResponse.model_validate(a) for a in alerts]


@router.get("/alerts/stats")
async def get_alert_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """获取告警统计"""
    start_time = datetime.utcnow() - timedelta(days=days)
    
    # 总数
    total = await db.scalar(
        select(func.count(AlertRecord.id)).where(AlertRecord.alert_time >= start_time)
    )
    
    # 按状态统计
    active = await db.scalar(
        select(func.count(AlertRecord.id)).where(
            and_(AlertRecord.alert_time >= start_time, AlertRecord.status == "active")
        )
    )
    
    acknowledged = await db.scalar(
        select(func.count(AlertRecord.id)).where(
            and_(AlertRecord.alert_time >= start_time, AlertRecord.status == "acknowledged")
        )
    )
    
    resolved = await db.scalar(
        select(func.count(AlertRecord.id)).where(
            and_(AlertRecord.alert_time >= start_time, AlertRecord.status == "resolved")
        )
    )
    
    # 按级别统计
    by_severity = {}
    for severity in ["P1", "P2", "P3", "P4"]:
        count = await db.scalar(
            select(func.count(AlertRecord.id)).where(
                and_(AlertRecord.alert_time >= start_time, AlertRecord.severity == severity)
            )
        )
        by_severity[severity] = count or 0
    
    return {
        "total": total or 0,
        "active": active or 0,
        "acknowledged": acknowledged or 0,
        "resolved": resolved or 0,
        "by_severity": by_severity
    }


@router.get("/charts/alert-trend", response_model=DashboardChart)
async def get_alert_trend_chart(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """获取告警趋势图"""
    start_time = datetime.utcnow() - timedelta(days=days)
    
    # 按日期统计告警
    result = await db.execute(
        select(
            func.date(AlertRecord.alert_time).label("date"),
            func.count(AlertRecord.id).label("count")
        )
        .where(AlertRecord.alert_time >= start_time)
        .group_by(func.date(AlertRecord.alert_time))
        .order_by("date")
    )
    
    rows = result.all()
    
    dates = [str(row.date) for row in rows]
    counts = [row.count for row in rows]
    
    return DashboardChart(
        name="告警趋势",
        type="line",
        categories=dates,
        series=[{"name": "告警数", "data": counts}]
    )


@router.get("/charts/metric-status")
async def get_metric_status_chart(db: AsyncSession = Depends(get_db)):
    """获取指标状态分布图"""
    # 按类别统计指标
    result = await db.execute(
        select(
            MetricDefinition.category,
            func.count(MetricDefinition.id).label("count")
        )
        .group_by(MetricDefinition.category)
    )
    
    rows = result.all()
    
    categories = [row.category or "未分类" for row in rows]
    series = [{"name": "指标数", "data": [row.count for row in rows]}]
    
    return DashboardChart(
        name="指标分布",
        type="pie",
        categories=categories,
        series=series
    )


@router.get("/system/health")
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """获取系统健康状态"""
    # 检查数据源状态
    result = await db.execute(
        select(DataSource)
    )
    sources = result.scalars().all()
    
    healthy = sum(1 for s in sources if s.status == "active")
    total = len(sources)
    
    # 检查活跃告警
    active_alerts = await db.scalar(
        select(func.count(AlertRecord.id)).where(AlertRecord.status == "active")
    )
    
    return {
        "overall_status": "healthy" if active_alerts == 0 else "warning",
        "data_sources": {
            "total": total,
            "healthy": healthy,
            "status": "all_healthy" if healthy == total else "partial_healthy"
        },
        "active_alerts": active_alerts,
        "timestamp": datetime.utcnow().isoformat()
    }
