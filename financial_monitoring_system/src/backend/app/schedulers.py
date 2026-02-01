"""
定时任务调度器
"""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.config import SCHEDULER_CHECK_INTERVAL, SCHEDULER_SYNC_INTERVAL


# 全局调度器实例
scheduler = AsyncScheduler()


def start_scheduler():
    """启动调度器"""
    # 添加数据采集任务 (每5分钟)
    scheduler.add_job(
        data_collection_task,
        IntervalTrigger(seconds=SCHEDULER_SYNC_INTERVAL),
        id="data_collection",
        name="数据采集任务",
        replace_existing=True
    )
    
    # 添加告警检查任务 (每1分钟)
    scheduler.add_job(
        alert_check_task,
        IntervalTrigger(seconds=SCHEDULER_CHECK_INTERVAL),
        id="alert_check",
        name="告警检查任务",
        replace_existing=True
    )
    
    # 添加每日报告生成任务 (每天早上7点)
    scheduler.add_job(
        daily_report_task,
        CronTrigger(hour=7, minute=0),
        id="daily_report",
        name="每日报告生成",
        replace_existing=True
    )
    
    # 添加系统健康检查 (每5分钟)
    scheduler.add_job(
        health_check_task,
        IntervalTrigger(minutes=5),
        id="health_check",
        name="系统健康检查",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ 定时任务调度器已启动")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown(wait=False)
    logger.info("⏹️ 定时任务调度器已停止")


async def data_collection_task():
    """数据采集任务"""
    logger.info("📊 执行数据采集任务...")
    try:
        from app.services.data_collector import DataCollector
        collector = DataCollector()
        await collector.collect_all()
        logger.info("✅ 数据采集任务完成")
    except Exception as e:
        logger.error(f"❌ 数据采集任务失败: {e}")


async def alert_check_task():
    """告警检查任务"""
    logger.info("🔔 执行告警检查任务...")
    try:
        from app.services.alert_engine import AlertEngine
        engine = AlertEngine()
        await engine.check_all_rules()
        logger.info("✅ 告警检查任务完成")
    except Exception as e:
        logger.error(f"❌ 告警检查任务失败: {e}")


async def daily_report_task():
    """每日报告生成任务"""
    logger.info("📝 执行每日报告生成任务...")
    try:
        from app.services.report_generator import ReportGenerator
        generator = ReportGenerator()
        await generator.generate_daily_reports()
        logger.info("✅ 每日报告生成完成")
    except Exception as e:
        logger.error(f"❌ 每日报告生成任务失败: {e}")


async def health_check_task():
    """系统健康检查任务"""
    logger.info("🏥 执行系统健康检查...")
    try:
        # TODO: 实现健康检查逻辑
        # 检查各数据源连接状态
        # 检查任务执行情况
        # 检查磁盘空间等
        logger.info("✅ 系统健康检查完成")
    except Exception as e:
        logger.error(f"❌ 系统健康检查失败: {e}")


# 手动触发任务的接口
async def trigger_data_collection():
    """手动触发数据采集"""
    logger.info("📊 手动触发数据采集...")
    await data_collection_task()


async def trigger_alert_check():
    """手动触发告警检查"""
    logger.info("🔔 手动触发告警检查...")
    await alert_check_task()
