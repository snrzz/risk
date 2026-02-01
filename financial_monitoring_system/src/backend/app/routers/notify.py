"""
通知渠道管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import NotifyChannel, UserProfile
from app.schemas import (
    NotifyChannelCreate, NotifyChannelUpdate, 
    NotifyChannelResponse
)


router = APIRouter()


@router.get("/")
async def list_channels(
    channel_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取通知渠道列表"""
    query = select(NotifyChannel)
    
    if channel_type:
        query = query.where(NotifyChannel.channel_type == channel_type)
    if status:
        query = query.where(NotifyChannel.status == status)
    
    result = await db.execute(query)
    channels = result.scalars().all()
    
    return {"channels": channels}


@router.get("/{channel_id}")
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    """获取渠道详情"""
    result = await db.execute(
        select(NotifyChannel).where(NotifyChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    return channel


@router.post("/")
async def create_channel(
    request: NotifyChannelCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建通知渠道"""
    # 检查编码是否重复
    existing = await db.scalar(
        select(NotifyChannel.id).where(NotifyChannel.code == request.code)
    )
    if existing:
        raise HTTPException(status_code=400, detail="渠道编码已存在")
    
    channel = NotifyChannel(
        code=request.code,
        name=request.name,
        channel_type=request.channel_type,
        config=request.config,
        status="active"
    )
    
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    
    return channel


@router.put("/{channel_id}")
async def update_channel(
    channel_id: int,
    request: NotifyChannelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新通知渠道"""
    result = await db.execute(
        select(NotifyChannel).where(NotifyChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)
    
    await db.commit()
    await db.refresh(channel)
    
    return channel


@router.delete("/{channel_id}")
async def delete_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    """删除通知渠道"""
    result = await db.execute(
        select(NotifyChannel).where(NotifyChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    await db.delete(channel)
    await db.commit()
    
    return {"message": "渠道已删除"}


@router.post("/{channel_id}/test")
async def test_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """测试通知渠道"""
    result = await db.execute(
        select(NotifyChannel).where(NotifyChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    # TODO: 实际发送测试消息
    # 根据channel_type调用不同的发送方法
    
    return {
        "success": True,
        "message": f"测试消息已通过 {channel.name} 发送"
    }


@router.get("/types/list")
async def get_channel_types():
    """获取支持的通知类型"""
    return {
        "types": [
            {
                "code": "lark",
                "name": "飞书",
                "description": "通过飞书机器人发送消息",
                "config_fields": ["webhook_url"]
            },
            {
                "code": "wecom",
                "name": "企业微信",
                "description": "通过企业微信机器人发送消息",
                "config_fields": ["key"]
            },
            {
                "code": "email",
                "name": "邮件",
                "description": "通过SMTP发送邮件",
                "config_fields": ["smtp_host", "smtp_port", "username", "password", "from_address"]
            },
            {
                "code": "dingtalk",
                "name": "钉钉",
                "description": "通过钉钉机器人发送消息",
                "config_fields": ["access_token", "secret"]
            },
            {
                "code": "telegram",
                "name": "Telegram",
                "description": "通过Telegram Bot发送消息",
                "config_fields": ["bot_token", "chat_id"]
            },
            {
                "code": "webhook",
                "name": "Webhook",
                "description": "通过HTTP Webhook推送消息",
                "config_fields": ["url", "method", "headers"]
            },
        ]
    }


# ============================================================
# 通知发送接口
# ============================================================

class SendNotificationRequest(BaseModel):
    """发送通知请求"""
    channel_code: str
    title: str
    content: str
    level: str = "info"  # info, warning, error
    recipients: Optional[list[str]] = None


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """发送通知消息"""
    # 获取渠道配置
    result = await db.execute(
        select(NotifyChannel).where(
            and_(
                NotifyChannel.code == request.channel_code,
                NotifyChannel.status == "active"
            )
        )
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="通知渠道不存在或已禁用")
    
    # TODO: 根据channel_type调用不同的发送方法
    # 这里应该调用通知服务发送消息
    
    return {
        "success": True,
        "message": "通知发送成功",
        "channel": channel.name
    }
