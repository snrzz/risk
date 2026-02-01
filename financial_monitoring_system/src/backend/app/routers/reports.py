"""
报告管理路由
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ReportTemplate, ReportRecord
from app.schemas import (
    ReportTemplateCreate, ReportTemplateUpdate, 
    ReportTemplateResponse, ReportRecordResponse,
    ReportGenerateRequest
)


router = APIRouter()


@router.get("/templates")
async def list_templates(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取报告模板列表"""
    query = select(ReportTemplate)
    
    conditions = []
    if report_type:
        conditions.append(ReportTemplate.report_type == report_type)
    if status:
        conditions.append(ReportTemplate.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """获取模板详情"""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return template


@router.post("/templates")
async def create_template(
    request: ReportTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建报告模板"""
    # 检查编码是否重复
    existing = await db.scalar(
        select(ReportTemplate.id).where(ReportTemplate.code == request.code)
    )
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    template = ReportTemplate(
        code=request.code,
        name=request.name,
        report_type=request.report_type,
        content_template=request.content_template,
        schedule_cron=request.schedule_cron,
        recipients=request.recipients,
        notify_channels=request.notify_channels,
        status="active"
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    request: ReportTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新报告模板"""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    
    return template


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """删除报告模板"""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "模板已删除"}


@router.get("/records")
async def list_records(
    template_code: Optional[str] = None,
    status: Optional[str] = None,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取报告记录列表"""
    query = select(ReportRecord)
    
    conditions = []
    if template_code:
        conditions.append(ReportRecord.template_code == template_code)
    if status:
        conditions.append(ReportRecord.status == status)
    if start_time:
        conditions.append(ReportRecord.report_time >= start_time)
    if end_time:
        conditions.append(ReportRecord.report_time <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(ReportRecord.report_time.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # 总数
    count_query = select(func.count(ReportRecord.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    return {
        "items": records,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """手动生成报告"""
    # 获取模板
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == request.template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 创建报告记录
    record = ReportRecord(
        template_id=request.template_id,
        template_code=template.code,
        report_time=datetime.utcnow(),
        time_range_start=request.time_range_start,
        time_range_end=request.time_range_end,
        recipients=request.recipients or template.recipients,
        status="generating"
    )
    
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    # TODO: 调用报告生成服务异步生成报告
    # 这里应该将任务加入队列
    
    return {
        "message": "报告生成任务已创建",
        "record_id": record.id
    }


@router.get("/records/{record_id}")
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """获取报告记录详情"""
    result = await db.execute(
        select(ReportRecord).where(ReportRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record


@router.get("/types")
async def get_report_types():
    """获取报告类型"""
    return {
        "types": [
            {"code": "daily", "name": "日报", "description": "每日运营报告"},
            {"code": "weekly", "name": "周报", "description": "每周运营报告"},
            {"code": "monthly", "name": "月报", "description": "每月运营报告"},
            {"code": "custom", "name": "自定义", "description": "自定义报告"},
        ]
    }
