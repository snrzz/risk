from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction, models
from django.db.models import Sum, Avg, Max
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='tasks.sync_risk_indicators')
def sync_risk_indicators(self):
    """同步风险指标数据"""
    from risk.models import Portfolio, RiskIndicator
    
    logger.info("开始同步风险指标数据")
    
    try:
        today = timezone.now().date()
        portfolios = Portfolio.objects.filter(status='active')
        
        for portfolio in portfolios:
            # 检查是否已有今日指标
            if RiskIndicator.objects.filter(
                portfolio=portfolio,
                indicator_date=today
            ).exists():
                logger.info(f"组合{portfolio.code}今日指标已存在，跳过")
                continue
            
            # 模拟生成风险指标（实际应从数据源获取）
            indicator = RiskIndicator.objects.create(
                portfolio=portfolio,
                indicator_date=today,
                daily_return=Decimal('0.0012'),
                cumulative_return=Decimal('0.0523'),
                annualized_return=Decimal('0.1234'),
                daily_volatility=Decimal('0.0123'),
                annualized_volatility=Decimal('0.1987'),
                max_drawdown=Decimal('-0.0523'),
                value_at_risk=Decimal('0.0234'),
                sharpe_ratio=Decimal('0.6523'),
                sortino_ratio=Decimal('0.8923'),
                information_ratio=Decimal('0.1234'),
                industry_concentration=Decimal('0.2345'),
                stock_concentration=Decimal('0.3456'),
                top10_holdings_ratio=Decimal('0.4523')
            )
            
            logger.info(f"组合{portfolio.code}风险指标已生成")
        
        # 清除缓存
        cache.delete('risk_indicators_latest')
        
        return {'status': 'success', 'portfolios_processed': portfolios.count()}
    
    except SoftTimeLimitExceeded:
        logger.error("同步风险指标任务超时")
        return {'status': 'error', 'message': '任务超时'}
    except Exception as e:
        logger.error(f"同步风险指标失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, name='tasks.check_risk_alerts')
def check_risk_alerts(self):
    """检查风险预警"""
    from risk.models import Portfolio, RiskIndicator, RiskAlert
    
    logger.info("开始检查风险预警")
    
    try:
        today = timezone.now().date()
        
        # 定义风险阈值配置
        THRESHOLDS = {
            'max_drawdown': {'max': Decimal('-0.1'), 'severity': 'critical'},
            'value_at_risk': {'max': Decimal('0.05'), 'severity': 'warning'},
            'sharpe_ratio': {'min': Decimal('0.5'), 'severity': 'warning'},
            'industry_concentration': {'max': Decimal('0.3'), 'severity': 'warning'},
            'stock_concentration': {'max': Decimal('0.1'), 'severity': 'warning'},
        }
        
        alerts_created = 0
        
        for portfolio in Portfolio.objects.filter(status='active'):
            latest_indicator = RiskIndicator.objects.filter(
                portfolio=portfolio
            ).order_by('-indicator_date').first()
            
            if not latest_indicator:
                continue
            
            for field, config in THRESHOLDS.items():
                value = getattr(latest_indicator, field)
                if value is None:
                    continue
                
                # 检查是否触发阈值
                triggered = False
                if 'max' in config and value > config['max']:
                    triggered = True
                elif 'min' in config and value < config['min']:
                    triggered = True
                
                if triggered:
                    # 检查是否已存在未处理的预警
                    existing = RiskAlert.objects.filter(
                        portfolio=portfolio,
                        indicator_name=field,
                        status='pending'
                    ).exists()
                    
                    if not existing:
                        RiskAlert.objects.create(
                            alert_type='threshold',
                            portfolio=portfolio,
                            severity=config['severity'],
                            title=f"组合{portfolio.code} - {field}预警",
                            content=f"{field}指标触发阈值，当前值: {value}, 阈值: {config.get('max') or config.get('min')}",
                            indicator_name=field,
                            indicator_value=value,
                            threshold=config.get('max') or config.get('min')
                        )
                        alerts_created += 1
        
        logger.info(f"检查风险预警完成，新增{alerts_created}条预警")
        return {'status': 'success', 'alerts_created': alerts_created}
    
    except Exception as e:
        logger.error(f"检查风险预警失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, name='tasks.export_daily_report')
def export_daily_report(self, date=None):
    """导出日报"""
    from risk.models import Portfolio, RiskIndicator, Trade, RiskAlert
    from django.core.files.base import ContentFile
    from django.core import mail
    import csv
    from io import StringIO
    
    logger.info("开始导出日报")
    
    try:
        if date is None:
            date = timezone.now().date()
        
        # 生成CSV报告
        output = StringIO()
        writer = csv.writer(output)
        
        # 标题
        writer.writerow(['风险日报', str(date)])
        writer.writerow([])
        
        # 组合汇总
        writer.writerow(['一、组合概况'])
        writer.writerow(['组合代码', '组合名称', '资产规模', '状态'])
        for portfolio in Portfolio.objects.filter(status='active'):
            writer.writerow([
                portfolio.code, portfolio.name,
                portfolio.asset_scale, portfolio.status
            ])
        writer.writerow([])
        
        # 风险指标
        writer.writerow(['二、风险指标'])
        writer.writerow(['组合代码', '日收益率', '年化收益率', '夏普比率', '最大回撤', 'VaR'])
        for portfolio in Portfolio.objects.filter(status='active'):
            indicator = RiskIndicator.objects.filter(
                portfolio=portfolio
            ).order_by('-indicator_date').first()
            if indicator:
                writer.writerow([
                    portfolio.code, indicator.daily_return,
                    indicator.annualized_return, indicator.sharpe_ratio,
                    indicator.max_drawdown, indicator.value_at_risk
                ])
        writer.writerow([])
        
        # 交易统计
        writer.writerow(['三、今日交易'])
        today_trades = Trade.objects.filter(trade_date=date)
        writer.writerow(['总交易笔数', '总成交金额'])
        writer.writerow([today_trades.count(), today_trades.aggregate(total=Sum('amount'))['total']])
        writer.writerow([])
        
        # 预警统计
        writer.writerow(['四、风险预警'])
        alerts = RiskAlert.objects.filter(alert_time__date=date)
        writer.writerow(['待处理预警数', '严重预警数'])
        writer.writerow([
            alerts.filter(status='pending').count(),
            alerts.filter(severity='critical').count()
        ])
        
        # 保存文件
        report_content = output.getvalue()
        filename = f"risk_report_{date}.csv"
        
        # 这里可以添加邮件发送逻辑
        # with mail.get_connection() as connection:
        #     mail.send_mail(...)
        
        logger.info(f"日报导出完成: {filename}")
        return {'status': 'success', 'filename': filename}
    
    except Exception as e:
        logger.error(f"导出日报失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, name='tasks.cache_warmup')
def cache_warmup(self):
    """缓存预热"""
    from risk.models import Portfolio, RiskIndicator, RiskAlert
    from django.db.models import Max
    
    logger.info("开始缓存预热")
    
    try:
        # 缓存组合列表
        portfolios = Portfolio.objects.filter(status='active').values('id', 'code', 'name')
        cache.set('active_portfolios', list(portfolios), 300)
        
        # 缓存最新风险指标
        latest_indicators = RiskIndicator.objects.filter(
            id__in=RiskIndicator.objects.values('portfolio').annotate(
                latest_id=Max('id')
            ).values('latest_id')
        ).select_related('portfolio')
        
        indicators_data = [{
            'portfolio_code': i.portfolio.code,
            'portfolio_name': i.portfolio.name,
            'daily_return': str(i.daily_return),
            'sharpe_ratio': str(i.sharpe_ratio),
            'max_drawdown': str(i.max_drawdown),
        } for i in latest_indicators]
        
        cache.set('risk_indicators_latest', indicators_data, 300)
        
        # 缓存预警统计
        alert_stats = {
            'pending': RiskAlert.objects.filter(status='pending').count(),
            'critical': RiskAlert.objects.filter(status='pending', severity='critical').count()
        }
        cache.set('alert_statistics', alert_stats, 300)
        
        logger.info("缓存预热完成")
        return {'status': 'success'}
    
    except Exception as e:
        logger.error(f"缓存预热失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, name='tasks.detect_abnormal_trades')
def detect_abnormal_trades(self, date=None):
    """检测异常交易"""
    from risk.models import Trade
    from django.db.models import Avg
    
    logger.info("开始检测异常交易")
    
    try:
        if date is None:
            date = timezone.now().date()
        
        # 获取今日交易统计
        today_trades = Trade.objects.filter(trade_date=date)
        if not today_trades.exists():
            return {'status': 'success', 'message': '今日无交易'}
        
        avg_price = today_trades.aggregate(avg=Avg('price'))['avg']
        avg_amount = today_trades.aggregate(avg=Avg('amount'))['avg']
        
        # 标记异常交易
        abnormal_threshold_price = avg_price * Decimal('1.5')  # 价格偏离50%以上
        abnormal_threshold_amount = avg_amount * Decimal('3')  # 金额偏离3倍以上
        
        abnormal_trades = today_trades.filter(
            models.Q(price__gt=abnormal_threshold_price) |
            models.Q(amount__gt=abnormal_threshold_amount)
        )
        
        updated = abnormal_trades.update(
            is_abnormal=True,
            abnormal_reason='价格或金额偏离正常范围'
        )
        
        logger.info(f"检测到{updated}条异常交易")
        return {'status': 'success', 'abnormal_count': updated}
    
    except Exception as e:
        logger.error(f"检测异常交易失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}
