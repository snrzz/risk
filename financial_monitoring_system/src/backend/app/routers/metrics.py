"""
指标数据路由
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import MetricDefinition, MetricData
from app.schemas import MetricDataResponse, MetricDataPoint, BaseResponse


router = APIRouter()


@router.get("/")
async def list_metrics(
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取指标列表"""
    query = select(MetricDefinition)
    
    if category:
        query = query.where(MetricDefinition.category == category)
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # 总数
    count_query = select(func.count(MetricDefinition.id))
    if category:
        count_query = count_query.where(MetricDefinition.category == category)
    total = await db.scalar(count_query)
    
    return {
        "items": metrics,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{metric_code}")
async def get_metric(metric_code: str, db: AsyncSession = Depends(get_db)):
    """获取指标详情"""
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.code == metric_code)
    )
    metric = result.scalar_one_or_none()
    
    if not metric:
        raise HTTPException(status_code=404, detail="指标不存在")
    
    return metric


@router.get("/{metric_code}/data")
async def get_metric_data(
    metric_code: str,
    start_time: datetime,
    end_time: datetime = None,
    aggregation: Optional[str] = Query(None, regex="^(hour|day|week|month)$"),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """获取指标历史数据"""
    if end_time is None:
        end_time = datetime.utcnow()
    
    # 验证指标存在
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.code == metric_code)
    )
    metric = result.scalar_one_or_none()
    
    if not metric:
        raise HTTPException(status_code=404, detail="指标不存在")
    
    # 查询数据
    query = select(MetricData).where(
        and_(
            MetricData.metric_code == metric_code,
            MetricData.data_time >= start_time,
            MetricData.data_time <= end_time
        )
    ).order_by(MetricData.data_time.desc()).limit(limit)
    
    result = await db.execute(query)
    data_points = result.scalars().all()
    
    return {
        "metric_code": metric_code,
        "data": [
            {
                "metric_code": d.metric_code,
                "timestamp": d.data_time.isoformat(),
                "value": d.value
            }
            for d in data_points
        ],
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }


@router.get("/data/realtime")
async def get_realtime_metrics(
    metric_codes: List[str] = Query(..., description="指标编码列表"),
    db: AsyncSession = Depends(get_db)
):
    """获取实时指标最新值"""
    latest_data = []
    
    for code in metric_codes:
        # 获取每个指标的最新数据
        result = await db.execute(
            select(MetricData)
            .where(MetricData.metric_code == code)
            .order_by(MetricData.data_time.desc())
            .limit(1)
        )
        data = result.scalar_one_or_none()
        
        if data:
            latest_data.append({
                "metric_code": code,
                "timestamp": data.data_time.isoformat(),
                "value": data.value,
                "status": data.status
            })
    
    return {"metrics": latest_data}


@router.get("/categories")
async def get_metric_categories(db: AsyncSession = Depends(get_db)):
    """获取指标分类"""
    result = await db.execute(
        select(MetricDefinition.category, func.count(MetricDefinition.id))
        .group_by(MetricDefinition.category)
    )
    
    categories = [{"name": row[0] or "未分类", "count": row[1]} for row in result.all()]
    
    return {"categories": categories}
