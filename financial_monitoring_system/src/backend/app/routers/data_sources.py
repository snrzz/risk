"""
数据源管理路由
"""
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DataSource, SyncLog
from app.schemas import DataSourceCreate, DataSourceUpdate, DataSourceResponse


router = APIRouter()


@router.get("/")
async def list_datasources(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取数据源列表"""
    query = select(DataSource)
    
    if status:
        query = query.where(DataSource.status == status)
    if source_type:
        query = query.where(DataSource.source_type == source_type)
    
    # 分页
    query = query.order_by(DataSource.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    # 总数
    count_query = select(func.count(DataSource.id))
    total = await db.scalar(count_query)
    
    return {
        "items": sources,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.get("/{source_id}")
async def get_datasource(source_id: int, db: AsyncSession = Depends(get_db)):
    """获取数据源详情"""
    result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    return source


@router.post("/")
async def create_datasource(
    request: DataSourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建数据源"""
    # 检查编码是否重复
    existing = await db.scalar(
        select(DataSource.id).where(DataSource.code == request.code)
    )
    if existing:
        raise HTTPException(status_code=400, detail="数据源编码已存在")
    
    source = DataSource(
        name=request.name,
        code=request.code,
        source_type=request.source_type,
        connection_info=request.connection_info,
        config_schema=request.config_schema,
        sync_interval=request.sync_interval,
        status="active"
    )
    
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    return source


@router.put("/{source_id}")
async def update_datasource(
    source_id: int,
    request: DataSourceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新数据源"""
    result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)
    
    await db.commit()
    await db.refresh(source)
    
    return source


@router.delete("/{source_id}")
async def delete_datasource(source_id: int, db: AsyncSession = Depends(get_db)):
    """删除数据源"""
    result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    await db.delete(source)
    await db.commit()
    
    return {"message": "数据源已删除"}


@router.post("/{source_id}/test")
async def test_datasource_connection(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """测试数据源连接"""
    result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # TODO: 实现具体的连接测试逻辑
    # 这里需要根据source_type调用不同的测试方法
    
    # 模拟测试结果
    test_result = {
        "success": True,
        "message": "连接测试成功",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return test_result


@router.post("/{source_id}/sync")
async def trigger_sync(
    source_id: int,
    sync_type: str = Query("incremental", regex="^(full|incremental)$"),
    db: AsyncSession = Depends(get_db)
):
    """手动触发数据同步"""
    result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 创建同步日志
    sync_log = SyncLog(
        data_source_id=source_id,
        sync_type=sync_type,
        start_time=datetime.utcnow(),
        status="running"
    )
    db.add(sync_log)
    await db.commit()
    await db.refresh(sync_log)
    
    # TODO: 触发实际的同步任务
    # 这里应该调用数据采集服务执行同步
    
    # 更新数据源状态
    source.last_sync_time = datetime.utcnow()
    source.status = "active"
    await db.commit()
    
    return {
        "message": "同步任务已启动",
        "sync_log_id": sync_log.id
    }


@router.get("/{source_id}/sync-logs")
async def get_sync_logs(
    source_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取同步日志"""
    result = await db.execute(
        select(SyncLog)
        .where(SyncLog.data_source_id == source_id)
        .order_by(SyncLog.start_time.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return {"logs": logs}


@router.get("/types")
async def get_source_types():
    """获取支持的数据源类型"""
    return {
        "types": [
            {"code": "database_view", "name": "数据库视图", "description": "通过SQL视图获取数据"},
            {"code": "csv_file", "name": "CSV文件", "description": "监控CSV格式文件"},
            {"code": "excel_file", "name": "Excel文件", "description": "监控Excel格式文件"},
            {"code": "json_file", "name": "JSON文件", "description": "监控JSON格式文件"},
            {"code": "xml_file", "name": "XML文件", "description": "监控XML格式文件"},
            {"code": "log_file", "name": "日志文件", "description": "监控日志文件"},
        ]
    }
