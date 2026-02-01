"""
告警规则管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AlertRule, MetricDefinition
from app.schemas import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse


router = APIRouter()


@router.get("/")
async def list_rules(
    metric_code: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    enabled: bool = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取告警规则列表"""
    query = select(AlertRule)
    
    conditions = []
    if metric_code:
        conditions.append(AlertRule.metric_code == metric_code)
    if severity:
        conditions.append(AlertRule.severity == severity)
    if status:
        conditions.append(AlertRule.status == status)
    if enabled is not None:
        conditions.append(AlertRule.enabled == enabled)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 分页
    query = query.order_by(AlertRule.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    # 总数
    count_query = select(func.count(AlertRule.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    return {
        "items": rules,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.get("/{rule_id}")
async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """获取规则详情"""
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    return rule


@router.post("/")
async def create_rule(
    request: AlertRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建告警规则"""
    # 检查指标是否存在
    metric = await db.scalar(
        select(MetricDefinition.id).where(MetricDefinition.code == request.metric_code)
    )
    if not metric:
        raise HTTPException(status_code=400, detail="指标不存在")
    
    # 检查编码是否重复
    existing = await db.scalar(
        select(AlertRule.id).where(AlertRule.code == request.code)
    )
    if existing:
        raise HTTPException(status_code=400, detail="规则编码已存在")
    
    rule = AlertRule(
        code=request.code,
        name=request.name,
        description=request.description,
        metric_code=request.metric_code,
        condition_type=request.condition_type,
        condition_config=request.condition_config,
        severity=request.severity,
        notify_channels=request.notify_channels,
        notify_users=request.notify_users,
        cooldown_minutes=request.cooldown_minutes,
        status="active",
        enabled=True
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return rule


@router.put("/{rule_id}")
async def update_rule(
    rule_id: int,
    request: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新告警规则"""
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    await db.commit()
    await db.refresh(rule)
    
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """删除告警规则"""
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    await db.delete(rule)
    await db.commit()
    
    return {"message": "规则已删除"}


@router.post("/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    enabled: bool,
    db: AsyncSession = Depends(get_db)
):
    """启用/禁用规则"""
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    rule.enabled = enabled
    await db.commit()
    
    return {"message": f"规则已{'启用' if enabled else '禁用'}"}


@router.get("/templates/list")
async def get_rule_templates():
    """获取规则模板"""
    return {
        "templates": [
            {
                "code": "threshold_high",
                "name": "阈值告警-高于",
                "description": "当指标值超过阈值时触发",
                "condition_type": "threshold",
                "condition_config": {
                    "operator": ">",
                    "threshold": 100
                }
            },
            {
                "code": "threshold_low",
                "name": "阈值告警-低于",
                "description": "当指标值低于阈值时触发",
                "condition_type": "threshold",
                "condition_config": {
                    "operator": "<",
                    "threshold": 10
                }
            },
            {
                "code": "range",
                "name": "范围告警",
                "description": "当指标值超出指定范围时触发",
                "condition_type": "range",
                "condition_config": {
                    "min": 10,
                    "max": 100
                }
            },
            {
                "code": "change_rate",
                "name": "变化率告警",
                "description": "当指标变化率超过阈值时触发",
                "condition_type": "change_rate",
                "condition_config": {
                    "period": "1h",
                    "threshold": 0.1
                }
            },
            {
                "code": "trend",
                "name": "趋势告警",
                "description": "当指标趋势偏离时触发",
                "condition_type": "trend",
                "condition_config": {
                    "direction": "up",
                    "consecutive": 3,
                    "threshold": 0.05
                }
            }
        ]
    }
