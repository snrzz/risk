"""
报告生成服务
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from jinja2 import Template
import json
from loguru import logger

from app.database import get_db_context
from app.models import ReportTemplate, ReportRecord, MetricData, AlertRecord


class ReportGenerator:
    """报告生成器"""
    
    async def generate_daily_reports(self):
        """生成所有日报"""
        async with get_db_context() as db:
            from sqlalchemy import select
            
            # 获取所有日报模板
            result = await db.execute(
                select(ReportTemplate).where(
                    and_(
                        ReportTemplate.report_type == "daily",
                        ReportTemplate.status == "active"
                    )
                )
            )
            templates = result.scalars().all()
            
            yesterday = datetime.utcnow().date() - timedelta(days=1)
            time_range_start = datetime.combine(yesterday, datetime.min.time())
            time_range_end = datetime.combine(yesterday, datetime.max.time())
            
            for template in templates:
                try:
                    await self.generate_report(
                        db, template, 
                        time_range_start, time_range_end
                    )
                except Exception as e:
                    logger.error(f"生成日报模板 {template.code} 失败: {e}")
            
            await db.commit()
    
    async def generate_report(
        self,
        db,
        template: ReportTemplate,
        time_range_start: datetime,
        time_range_end: datetime
    ):
        """生成单个报告"""
        # 创建报告记录
        record = ReportRecord(
            template_id=template.id,
            template_code=template.code,
            report_time=datetime.utcnow(),
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            status="generating"
        )
        db.add(record)
        await db.commit()
        
        try:
            # 收集数据
            data = await self.collect_report_data(
                db, template, time_range_start, time_range_end
            )
            
            # 渲染模板
            content = self.render_template(template.content_template, data)
            
            # 保存报告
            record.content = content
            record.status = "generated"
            
            # TODO: 发送报告给收件人
            if template.notify_channels and template.recipients:
                await self.send_report(
                    db, template, record, content
                )
            
            await db.commit()
            logger.info(f"✅ 报告生成完成: {template.name}")
            
        except Exception as e:
            record.status = "failed"
            record.error_message = str(e)
            await db.commit()
            logger.error(f"❌ 报告生成失败: {template.name}, error: {e}")
    
    async def collect_report_data(
        self,
        db,
        template: ReportTemplate,
        time_range_start: datetime,
        time_range_end: datetime
    ) -> Dict[str, Any]:
        """收集报告数据"""
        data = {
            "report_time": datetime.utcnow().isoformat(),
            "time_range": {
                "start": time_range_start.isoformat(),
                "end": time_range_end.isoformat()
            }
        }
        
        from sqlalchemy import select, func
        
        # 1. 告警统计
        alert_result = await db.execute(
            select(
                func.count(AlertRecord.id),
                func.sum(AlertRecord.severity == "P1"),
                func.sum(AlertRecord.severity == "P2")
            )
            .where(
                and_(
                    AlertRecord.alert_time >= time_range_start,
                    AlertRecord.alert_time <= time_range_end
                )
            )
        )
        alert_stats = alert_result.first()
        data["alerts"] = {
            "total": alert_stats[0] or 0,
            "p1": alert_stats[1] or 0,
            "p2": alert_stats[2] or 0
        }
        
        # 2. 指标趋势 (需要从metric_data表获取)
        # TODO: 实现指标趋势数据收集
        
        # 3. 系统状态
        data["system_status"] = "healthy"
        
        return data
    
    def render_template(self, template_str: str, data: Dict) -> str:
        """渲染Jinja2模板"""
        template = Template(template_str)
        return template.render(**data)
    
    async def send_report(
        self,
        db,
        template: ReportTemplate,
        record: ReportRecord,
        content: str
    ):
        """发送报告"""
        # TODO: 实现报告发送逻辑
        logger.info(f"📧 准备发送报告 {template.name} 到 {template.recipients}")


class DailyReportBuilder:
    """日报构建器"""
    
    def __init__(self):
        self.sections = []
    
    def add_section(self, title: str, content: str):
        """添加报告章节"""
        self.sections.append({"title": title, "content": content})
    
    def build(self) -> str:
        """构建完整报告"""
        report = "# 金融风控监控日报\n\n"
        report += f"报告时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for section in self.sections:
            report += f"## {section['title']}\n\n"
            report += section['content']
            report += "\n\n"
        
        return report


class AlertReportBuilder:
    """告警报告构建器"""
    
    def __init__(self, time_range_start, time_range_end):
        self.time_range_start = time_range_start
        self.time_range_end = time_range_end
        self.alerts = []
    
    def add_alert(self, alert: AlertRecord):
        """添加告警"""
        self.alerts.append(alert)
    
    def build(self) -> str:
        """构建告警报告"""
        report = "## 告警概览\n\n"
        report += f"时间范围: {self.time_range_start} 至 {self.time_range_end}\n\n"
        report += f"告警总数: {len(self.alerts)}\n\n"
        
        # 按严重程度分组
        by_severity = {}
        for alert in self.alerts:
            if alert.severity not in by_severity:
                by_severity[alert.severity] = []
            by_severity[alert.severity].append(alert)
        
        for severity in ["P1", "P2", "P3", "P4"]:
            if severity in by_severity:
                report += f"### {severity} 级告警 ({len(by_severity[severity])}条)\n\n"
                for alert in by_severity[severity]:
                    report += f"- {alert.alert_time}: {alert.message}\n"
                report += "\n"
        
        return report
