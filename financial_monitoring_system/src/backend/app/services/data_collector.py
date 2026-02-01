"""
数据采集服务
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from loguru import logger

from app.database import get_db_context
from app.models import DataSource, MetricDefinition, MetricData, SyncLog


class DataCollector:
    """数据采集器"""
    
    def __init__(self):
        self.adapters = {
            "database_view": DatabaseViewAdapter(),
            "csv_file": CSVFileAdapter(),
            "excel_file": ExcelFileAdapter(),
            "json_file": JSONFileAdapter(),
        }
    
    async def collect_all(self):
        """采集所有数据源"""
        async with get_db_context() as db:
            # 获取所有活跃数据源
            from sqlalchemy import select
            result = await db.execute(
                select(DataSource).where(DataSource.status == "active")
            )
            sources = result.scalars().all()
            
            tasks = []
            for source in sources:
                task = self.collect_source(db, source)
                tasks.append(task)
            
            # 并发执行
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def collect_source(self, db, source: DataSource):
        """采集单个数据源"""
        logger.info(f"📥 开始采集数据源: {source.name} ({source.code})")
        
        sync_log = SyncLog(
            data_source_id=source.id,
            sync_type="incremental",
            start_time=datetime.utcnow(),
            status="running"
        )
        db.add(sync_log)
        await db.commit()
        
        try:
            # 获取适配器
            adapter = self.adapters.get(source.source_type)
            if not adapter:
                raise ValueError(f"不支持的数据源类型: {source.source_type}")
            
            # 执行采集
            raw_data = await adapter.fetch(source)
            
            # 处理数据
            metrics_data = await self.process_data(db, source, raw_data)
            
            # 保存指标数据
            for metric_code, value in metrics_data.items():
                metric_data = MetricData(
                    metric_code=metric_code,
                    data_time=datetime.utcnow(),
                    value=value,
                    raw_data=raw_data.get(metric_code),
                    status="normal"
                )
                db.add(metric_data)
            
            # 更新同步日志
            sync_log.end_time = datetime.utcnow()
            sync_log.status = "success"
            sync_log.records_processed = len(metrics_data)
            
            # 更新数据源状态
            source.last_sync_time = datetime.utcnow()
            source.status = "active"
            source.error_message = None
            
            await db.commit()
            logger.info(f"✅ 数据源 {source.name} 采集完成, 处理 {len(metrics_data)} 条指标")
            
        except Exception as e:
            logger.error(f"❌ 数据源 {source.name} 采集失败: {e}")
            sync_log.end_time = datetime.utcnow()
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            
            source.status = "error"
            source.error_message = str(e)
            
            await db.commit()
    
    async def process_data(self, db, source, raw_data: Dict) -> Dict[str, float]:
        """处理原始数据,提取指标值"""
        metrics_data = {}
        
        # 获取该数据源关联的指标
        from sqlalchemy import select
        result = await db.execute(
            select(MetricDefinition).where(
                MetricDefinition.data_source_id == source.id
            )
        )
        metrics = result.scalars().all()
        
        for metric in metrics:
            try:
                # 根据指标配置提取值
                value = self._extract_value(raw_data, metric)
                if value is not None:
                    metrics_data[metric.code] = value
            except Exception as e:
                logger.warning(f"提取指标 {metric.code} 值失败: {e}")
        
        return metrics_data
    
    def _extract_value(self, raw_data: Dict, metric) -> float:
        """从原始数据中提取指标值"""
        field_name = metric.field_name
        
        if metric.expression:
            # 使用表达式计算
            return self._evaluate_expression(raw_data, metric.expression)
        
        # 直接取值
        value = raw_data.get(field_name)
        if value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _evaluate_expression(self, raw_data: Dict, expression: str) -> float:
        """计算表达式"""
        # 替换变量
        expr = expression
        for key, value in raw_data.items():
            expr = expr.replace(f"{{{key}}}", str(value))
        
        # 安全计算
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            logger.warning(f"表达式计算失败: {expression}, error: {e}")
            return None


# ============================================================
# 数据源适配器
# ============================================================

class BaseAdapter:
    """适配器基类"""
    
    async def fetch(self, source) -> Dict[str, Any]:
        raise NotImplementedError


class DatabaseViewAdapter(BaseAdapter):
    """数据库视图适配器"""
    
    async def fetch(self, source) -> Dict[str, Any]:
        import aiosqlite
        from app.config import DATABASE_URL
        
        conn_info = source.connection_info or {}
        db_path = conn_info.get("path")
        
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM " + conn_info.get("view_name"))
            rows = await cursor.fetchall()
            
            if not rows:
                return {}
            
            # 返回第一行数据
            row = rows[0]
            return {key: row[key] for key in row.keys()}


class CSVFileAdapter(BaseAdapter):
    """CSV文件适配器"""
    
    async def fetch(self, source) -> Dict[str, Any]:
        import pandas as pd
        
        conn_info = source.connection_info or {}
        file_path = conn_info.get("path")
        
        if not file_path:
            return {}
        
        df = pd.read_csv(file_path)
        
        if df.empty:
            return {}
        
        # 返回最后一行
        row = df.iloc[-1]
        return row.to_dict()


class ExcelFileAdapter(BaseAdapter):
    """Excel文件适配器"""
    
    async def fetch(self, source) -> Dict[str, Any]:
        import pandas as pd
        
        conn_info = source.connection_info or {}
        file_path = conn_info.get("path")
        sheet_name = conn_info.get("sheet_name", 0)
        
        if not file_path:
            return {}
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        if df.empty:
            return {}
        
        row = df.iloc[-1]
        return row.to_dict()


class JSONFileAdapter(BaseAdapter):
    """JSON文件适配器"""
    
    async def fetch(self, source) -> Dict[str, Any]:
        import json
        
        conn_info = source.connection_info or {}
        file_path = conn_info.get("path")
        
        if not file_path:
            return {}
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data
