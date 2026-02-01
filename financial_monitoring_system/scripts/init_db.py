#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from app.database import engine, Base
from app import models


def init_database():
    """初始化数据库表"""
    print("🚀 开始初始化数据库...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("✅ 数据库表创建完成")
    print("\n已创建的表:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


def drop_database():
    """删除所有数据库表"""
    print("⚠️  即将删除所有数据库表...")
    confirm = input("确认继续? (输入 DELETE 确认): ")
    
    if confirm == "DELETE":
        Base.metadata.drop_all(bind=engine)
        print("✅ 数据库表已删除")
    else:
        print("已取消")


def seed_demo_data():
    """插入演示数据"""
    from sqlalchemy.orm import Session
    from app.models import (
        DataSource, MetricDefinition, AlertRule, 
        NotifyChannel, UserProfile
    )
    
    print("🌱 开始插入演示数据...")
    
    with Session(engine) as session:
        # 1. 创建数据源
        sources = [
            DataSource(
                name="O32投资交易系统",
                code="o32_trading",
                source_type="database_view",
                connection_info={"view_name": "v_o32_positions"},
                status="active"
            ),
            DataSource(
                name="估值核算系统",
                code="valuation_system",
                source_type="database_view",
                connection_info={"view_name": "v_valuation_daily"},
                status="active"
            ),
            DataSource(
                name="风险控制系统",
                code="risk_system",
                source_type="database_view",
                connection_info={"view_name": "v_risk_indicators"},
                status="active"
            ),
        ]
        session.add_all(sources)
        session.flush()
        
        # 2. 创建指标
        metrics = [
            MetricDefinition(
                code="o32_total_position",
                name="O32总持仓",
                category="trading",
                data_source_id=sources[0].id,
                field_name="total_value",
                unit="元",
                aggregation_type="last"
            ),
            MetricDefinition(
                code="o32_position_concentration",
                name="持仓集中度",
                category="trading",
                data_source_id=sources[0].id,
                field_name="concentration",
                unit="%",
                aggregation_type="last"
            ),
            MetricDefinition(
                code="valuation_nav",
                name="单位净值",
                category="valuation",
                data_source_id=sources[1].id,
                field_name="nav",
                unit="元",
                aggregation_type="last"
            ),
            MetricDefinition(
                code="risk_var_95",
                name="VaR (95%)",
                category="risk",
                data_source_id=sources[2].id,
                field_name="var_95",
                unit="元",
                aggregation_type="last"
            ),
        ]
        session.add_all(metrics)
        session.flush()
        
        # 3. 创建告警规则
        rules = [
            AlertRule(
                code="alert_position_concentration_high",
                name="持仓集中度过高",
                metric_code="o32_position_concentration",
                condition_type="threshold",
                condition_config={"operator": ">", "threshold": 30},
                severity="P2",
                notify_channels=["lark"],
                status="active",
                enabled=True
            ),
            AlertRule(
                code="alert_var_exceeded",
                name="VaR超标",
                metric_code="risk_var_95",
                condition_type="threshold",
                condition_config={"operator": ">", "threshold": 10000000},
                severity="P1",
                notify_channels=["lark", "email"],
                status="active",
                enabled=True
            ),
        ]
        session.add_all(rules)
        session.flush()
        
        # 4. 创建通知渠道
        channels = [
            NotifyChannel(
                code="lark_alerts",
                name="飞书告警群",
                channel_type="lark",
                config={"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"},
                status="active"
            ),
        ]
        session.add_all(channels)
        
        # 5. 创建管理员用户
        admin = UserProfile(
            username="admin",
            display_name="系统管理员",
            roles=["admin"],
            status="active"
        )
        session.add(admin)
        
        session.commit()
        print("✅ 演示数据插入完成")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("action", choices=["init", "drop", "seed", "reset"],
                        help="操作: init=初始化, drop=删除, seed=插入演示数据, reset=重置")
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_database()
    elif args.action == "drop":
        drop_database()
    elif args.action == "seed":
        seed_demo_data()
    elif args.action == "reset":
        drop_database()
        init_database()
        seed_demo_data()
