"""
通知服务
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

import httpx


class NotifyService:
    """通知服务"""
    
    def __init__(self):
        self.max_retry = 3
        self.retry_interval = 5  # 秒
    
    async def send(
        self,
        channel_type: str,
        config: Dict[str, Any],
        title: str,
        content: str,
        level: str = "info"
    ):
        """发送通知"""
        method = f"send_{channel_type}"
        send_func = getattr(self, method, None)
        
        if not send_func:
            logger.error(f"不支持的通知类型: {channel_type}")
            return False
        
        for attempt in range(self.max_retry):
            try:
                await send_func(config, title, content, level)
                logger.info(f"✅ 通知发送成功: {channel_type}")
                return True
            except Exception as e:
                logger.warning(f"通知发送失败 (尝试 {attempt + 1}/{self.max_retry}): {e}")
                if attempt < self.max_retry - 1:
                    await asyncio.sleep(self.retry_interval)
        
        logger.error(f"❌ 通知发送最终失败: {channel_type}")
        return False
    
    async def send_lark(
        self, 
        config: Dict[str, Any], 
        title: str, 
        content: str, 
        level: str = "info"
    ):
        """发送飞书通知"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("缺少飞书 webhook_url")
        
        # 根据级别设置颜色
        color_map = {
            "info": "blue",
            "warning": "yellow",
            "error": "red"
        }
        color = color_map.get(level, "blue")
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": f"**{title}**"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload)
    
    async def send_wecom(
        self, 
        config: Dict[str, Any], 
        title: str, 
        content: str, 
        level: str = "info"
    ):
        """发送企业微信通知"""
        key = config.get("key")
        if not key:
            raise ValueError("缺少企业微信 key")
        
        webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
        
        content_md = f"**{title}**\n\n{content}"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content_md,
                "mentioned_list": []
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload)
    
    async def send_email(
        self, 
        config: Dict[str, Any], 
        title: str, 
        content: str, 
        level: str = "info"
    ):
        """发送邮件通知"""
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        
        smtp_config = {
            "host": config.get("smtp_host", "localhost"),
            "port": config.get("smtp_port", 25),
            "username": config.get("username"),
            "password": config.get("password"),
            "from_address": config.get("from_address", "noreply@example.com"),
            "to_addresses": config.get("to_addresses", [])
        }
        
        if not smtp_config["to_addresses"]:
            raise ValueError("缺少收件人地址")
        
        # 构建邮件
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(title, 'utf-8')
        msg['From'] = smtp_config["from_address"]
        msg['To'] = ",".join(smtp_config["to_addresses"])
        
        # 发送邮件
        try:
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])
            if smtp_config.get("password"):
                server.login(smtp_config["username"], smtp_config["password"])
            server.sendmail(
                smtp_config["from_address"],
                smtp_config["to_addresses"],
                msg.as_string()
            )
            server.quit()
        except Exception as e:
            raise ValueError(f"邮件发送失败: {e}")
    
    async def send_dingtalk(
        self, 
        config: Dict[str, Any], 
        title: str, 
        content: str, 
        level: str = "info"
    ):
        """发送钉钉通知"""
        import time
        import hmac
        import hashlib
        import base64
        
        access_token = config.get("access_token")
        secret = config.get("secret")
        
        if not access_token:
            raise ValueError("缺少钉钉 access_token")
        
        webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
        
        # 如果有签名密钥
        if secret:
            timestamp = str(int(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            webhook_url += f"&timestamp={timestamp}&sign={sign}"
        
        content_md = f"**{title}**\n\n{content}"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content_md
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload)
    
    async def send_telegram(
        self, 
        config: Dict[str, Any], 
        title: str, 
        content: str, 
        level: str = "info"
    ):
        """发送Telegram通知"""
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")
        
        if not bot_token or not chat_id:
            raise ValueError("缺少 Telegram bot_token 或 chat_id")
        
        message = f"*{title}*\n\n{content}"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    
    async def send_webhook(
        self, 
        config: Dict[str, Any], 
        title: str, 
        content: str, 
        level: str = "info"
    ):
        """发送Webhook通知"""
        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        
        if not url:
            raise ValueError("缺少 webhook url")
        
        payload = {
            "title": title,
            "content": content,
            "level": level,
            "timestamp": str(datetime.utcnow())
        }
        
        async with httpx.AsyncClient() as client:
            request = client.build_request(method, url, json=payload, headers=headers)
            await client.send(request)
