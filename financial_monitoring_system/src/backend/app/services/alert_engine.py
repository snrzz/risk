"""
告警引擎服务
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
from loguru import logger

from app.database import get_db_context
from app.models import AlertRule, AlertRecord, MetricData


class AlertEngine:
    """告警引擎"""
    
    async def check_all_rules(self):
        """检查所有规则"""
        async with get_db_context() as db:
            from sqlalchemy import select
            
            # 获取所有启用的规则
            result = await db.execute(
                select(AlertRule).where(AlertRule.enabled == True)
            )
            rules = result.scalars().all()
            
            for rule in rules:
                try:
                    await self.check_rule(db, rule)
                except Exception as e:
                    logger.error(f"检查规则 {rule.code} 失败: {e}")
            
            await db.commit()
    
    async def check_rule(self, db, rule: AlertRule):
        """检查单个规则"""
        # 获取指标最新值
        metric_code = rule.metric_code
        latest_data = await self.get_latest_value(db, metric_code)
        
        if not latest_data:
            logger.debug(f"指标 {metric_code} 无数据, 跳过检查")
            return
        
        value = latest_data.value
        condition_config = rule.condition_config
        
        # 检查是否触发告警
        triggered, threshold = self.evaluate_condition(
            value, 
            rule.condition_type, 
            condition_config
        )
        
        if triggered:
            # 检查冷却时间
            if await self.is_in_cooldown(db, rule, metric_code):
                logger.debug(f"规则 {rule.code} 在冷却期内, 跳过")
                return
            
            # 创建告警记录
            await self.create_alert(db, rule, value, threshold)
            
            # 发送通知
            await self.send_notification(db, rule, value, threshold)
    
    async def get_latest_value(self, db, metric_code: str) -> MetricData:
        """获取指标最新值"""
        from sqlalchemy import select
        
        result = await db.execute(
            select(MetricData)
            .where(MetricData.metric_code == metric_code)
            .order_by(MetricData.data_time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    def evaluate_condition(
        self, 
        value: float, 
        condition_type: str, 
        config: Dict
    ) -> (bool, float):
        """评估条件"""
        if condition_type == "threshold":
            # 阈值告警
            operator = config.get("operator", ">")
            threshold = config.get("threshold", 0)
            
            if operator == ">":
                return value > threshold, threshold
            elif operator == ">=":
                return value >= threshold, threshold
            elif operator == "<":
                return value < threshold, threshold
            elif operator == "<=":
                return value <= threshold, threshold
            elif operator == "==":
                return value == threshold, threshold
        
        elif condition_type == "range":
            # 范围告警
            min_val = config.get("min", float("-inf"))
            max_val = config.get("max", float("inf"))
            
            out_of_range = value < min_val or value > max_val
            return out_of_range, f"{min_val}-{max_val}"
        
        elif condition_type == "change_rate":
            # 变化率告警
            threshold = config.get("threshold", 0)
            # TODO: 计算变化率并比较
        
        elif condition_type == "trend":
            # 趋势告警
            direction = config.get("direction", "up")
            consecutive = config.get("consecutive", 3)
            # TODO: 分析趋势
        
        return False, None
    
    async def is_in_cooldown(self, db, rule: AlertRule, metric_code: str) -> bool:
        """检查是否在冷却期内"""
        from sqlalchemy import select, and_
        
        # 获取该指标最近的告警
        cooldown_minutes = rule.cooldown_minutes
        threshold = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
        
        result = await db.execute(
            select(AlertRecord)
            .where(
                and_(
                    AlertRecord.metric_code == metric_code,
                    AlertRecord.rule_id == rule.id,
                    AlertRecord.alert_time >= threshold,
                    AlertRecord.status == "active"
                )
            )
        )
        
        recent_alert = result.scalar_one_or_none()
        return recent_alert is not None
    
    async def create_alert(
        self, 
        db, 
        rule: AlertRule, 
        value: float, 
        threshold: Any
    ):
        """创建告警记录"""
        # 生成告警消息
        message = self.generate_alert_message(rule, value, threshold)
        
        alert = AlertRecord(
            rule_id=rule.id,
            rule_code=rule.code,
            metric_code=rule.metric_code,
            alert_time=datetime.utcnow(),
            alert_value=value,
            threshold_value=float(threshold) if threshold else None,
            severity=rule.severity,
            message=message,
            status="active",
            notification_sent=False
        )
        
        db.add(alert)
        logger.info(f"🔔 告警已创建: {rule.name} - {message}")
    
    def generate_alert_message(
        self, 
        rule: AlertRule, 
        value: float, 
        threshold: Any
    ) -> str:
        """生成告警消息"""
        severity_map = {
            "P1": "🔴 紧急",
            "P2": "🟠 严重", 
            "P3": "🟡 警告",
            "P4": "🔵 提示"
        }
        
        severity_icon = severity_map.get(rule.severity, "⚪")
        
        message = f"{severity_icon} {rule.name}\n"
        message += f"指标: {rule.metric_code}\n"
        message += f"当前值: {value:.4f}\n"
        
        if threshold is not None:
            message += f"阈值: {threshold}\n"
        
        if rule.description:
            message += f"说明: {rule.description}"
        
        return message
    
    async def send_notification(
        self, 
        db, 
        rule: AlertRule, 
        value: float, 
        threshold: Any
    ):
        """发送告警通知"""
        # TODO: 实现通知发送
        # 根据notify_channels调用不同的通知服务
        
        message = self.generate_alert_message(rule, value, threshold)
        channels = rule.notify_channels or []
        
        logger.info(f"📨 准备发送通知到 {channels}: {message[:100]}...")
