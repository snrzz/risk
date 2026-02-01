"""
告警管理路由
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AlertRecord, AlertRule
from app.schemas import (
    AlertRecordResponse, AlertAckRequest, AlertResolveRequest,
    AlertStats, BaseResponse
)


router = APIRouter()


@router.get("/")
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    metric_code: Optional[str] = None,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取告警列表"""
    query = select(AlertRecord)
    
    conditions = []
    if status:
        conditions.append(AlertRecord.status == status)
    if severity:
        conditions.append(AlertRecord.severity == severity)
    if metric_code:
        conditions.append(AlertRecord.metric_code == metric_code)
    if start_time:
        conditions.append(AlertRecord.alert_time >= start_time)
    if end_time:
        conditions.append(AlertRecord.alert_time <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 分页
    query = query.order_by(AlertRecord.alert_time.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # 总数
    count_query = select(func.count(AlertRecord.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    return {
        "items": [AlertRecordResponse.model_validate(a) for a in alerts],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0
    }


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """获取告警统计"""
    start_time = datetime.utcnow() - datetime.timedelta(days=days)
    
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
    
    # 按指标统计TOP10
    result = await db.execute(
        select(
            AlertRecord.metric_code,
            func.count(AlertRecord.id).label("count")
        )
        .where(AlertRecord.alert_time >= start_time)
        .group_by(AlertRecord.metric_code)
        .order_by(func.count(AlertRecord.id).desc())
        .limit(10)
    )
    top_metrics = [{"code": row[0], "count": row[1]} for row in result.all()]
    
    return {
        "total": total or 0,
        "active": active or 0,
        "acknowledged": acknowledged or 0,
        "resolved": resolved or 0,
        "by_severity": by_severity,
        "top_metrics": top_metrics
    }


@router.get("/active")
async def get_active_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """获取活跃告警"""
    result = await db.execute(
        select(AlertRecord)
        .where(AlertRecord.status == "active")
        .order_by(
            and_(
                AlertRecord.severity.in_(["P1", "P2"]),
                AlertRecord.alert_time.desc()
            )
        )
        .limit(limit)
    )
    
    alerts = result.scalars().all()
    
    # 按严重程度分组
    grouped = {"P1": [], "P2": [], "P3": [], "P4": []}
    for alert in alerts:
        grouped[alert.severity].append(AlertRecordResponse.model_validate(alert))
    
    return {
        "grouped": grouped,
        "total": len(alerts)
    }


@router.post("/acknowledge")
async def acknowledge_alerts(
    request: AlertAckRequest,
    db: AsyncSession = Depends(get_db)
):
    """确认告警"""
    result = await db.execute(
        select(AlertRecord)
        .where(
            and_(
                AlertRecord.id.in_(request.record_ids),
                AlertRecord.status == "active"
            )
        )
    )
    alerts = result.scalars().all()
    
    now = datetime.utcnow()
    for alert in alerts:
        alert.status = "acknowledged"
        alert.acknowledged_by = request.acknowledged_by
        alert.acknowledged_at = now
        if request.message:
            alert.resolved_message = request.message
    
    await db.commit()
    
    return {"message": f"已确认 {len(alerts)} 条告警"}


@router.post("/resolve")
async def resolve_alerts(
    request: AlertResolveRequest,
    db: AsyncSession = Depends(get_db)
):
    """解决告警"""
    result = await db.execute(
        select(AlertRecord)
        .where(
            and_(
                AlertRecord.id.in_(request.record_ids),
                AlertRecord.status.in_(["active", "acknowledged"])
            )
        )
    )
    alerts = result.scalars().all()
    
    now = datetime.utcnow()
    for alert in alerts:
        alert.status = "resolved"
        alert.resolved_by = request.resolved_by
        alert.resolved_at = now
        alert.resolved_message = request.message
    
    await db.commit()
    
    return {"message": f"已解决 {len(alerts)} 条告警"}


@router.post("/bulk-update-status")
async def bulk_update_status(
    record_ids: List[int],
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """批量更新告警状态"""
    if status not in ["active", "acknowledged", "resolved", "expired"]:
        raise HTTPException(status_code=400, detail="无效状态")
    
    await db.execute(
        update(AlertRecord)
        .where(AlertRecord.id.in_(record_ids))
        .values(status=status)
    )
    
    await db.commit()
    
    return {"message": f"已更新 {len(record_ids)} 条告警状态"}


@router.get("/rules")
async def get_alert_rules(
    metric_code: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取告警规则列表"""
    query = select(AlertRule)
    
    conditions = []
    if metric_code:
        conditions.append(AlertRule.metric_code == metric_code)
    if status:
        conditions.append(AlertRule.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return {"rules": rules}
