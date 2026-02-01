from rest_framework import serializers
from .models import Portfolio, RiskIndicator, Trade, Holding, RiskAlert


class PortfolioSerializer(serializers.ModelSerializer):
    """组合序列化器"""
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'code', 'name', 'manager', 'portfolio_type',
            'status', 'asset_scale', 'remark',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RiskIndicatorSerializer(serializers.ModelSerializer):
    """风险指标序列化器"""
    portfolio_code = serializers.CharField(source='portfolio.code', read_only=True)
    portfolio_name = serializers.CharField(source='portfolio.name', read_only=True)
    
    class Meta:
        model = RiskIndicator
        fields = [
            'id', 'portfolio', 'portfolio_code', 'portfolio_name',
            'indicator_date',
            'daily_return', 'cumulative_return', 'annualized_return',
            'daily_volatility', 'annualized_volatility', 'max_drawdown', 'value_at_risk',
            'sharpe_ratio', 'sortino_ratio', 'information_ratio',
            'industry_concentration', 'stock_concentration', 'top10_holdings_ratio',
            'created_at'
        ]
        read_only_fields = ['created_at']


class TradeSerializer(serializers.ModelSerializer):
    """交易记录序列化器"""
    portfolio_code = serializers.CharField(source='portfolio.code', read_only=True)
    
    class Meta:
        model = Trade
        fields = [
            'id', 'portfolio', 'portfolio_code',
            'trade_type', 'security_type', 'security_code', 'security_name',
            'trade_date', 'trade_time',
            'quantity', 'price', 'amount',
            'commission', 'stamp_tax', 'transfer_fee',
            'status', 'is_abnormal', 'abnormal_reason', 'remark',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HoldingSerializer(serializers.ModelSerializer):
    """持仓信息序列化器"""
    portfolio_code = serializers.CharField(source='portfolio.code', read_only=True)
    
    class Meta:
        model = Holding
        fields = [
            'id', 'portfolio', 'portfolio_code',
            'holding_date',
            'security_type', 'security_code', 'security_name',
            'quantity', 'cost', 'cost_price', 'market_price', 'market_value',
            'unrealized_pnl', 'unrealized_pnl_ratio', 'holding_ratio',
            'created_at'
        ]
        read_only_fields = ['created_at']


class RiskAlertSerializer(serializers.ModelSerializer):
    """风险预警序列化器"""
    portfolio_code = serializers.CharField(source='portfolio.code', read_only=True)
    portfolio_name = serializers.CharField(source='portfolio.name', read_only=True)
    handled_by_name = serializers.CharField(source='handled_by.email', read_only=True)
    
    class Meta:
        model = RiskAlert
        fields = [
            'id', 'alert_type', 'portfolio', 'portfolio_code', 'portfolio_name',
            'severity', 'title', 'content',
            'indicator_name', 'indicator_value', 'threshold',
            'status',
            'handled_by', 'handled_by_name', 'handled_at', 'handle_comment',
            'notified', 'notification_time',
            'alert_time'
        ]
        read_only_fields = ['alert_time', 'notification_time']


class RiskAlertUpdateSerializer(serializers.ModelSerializer):
    """风险预警更新序列化器"""
    
    class Meta:
        model = RiskAlert
        fields = ['status', 'handle_comment']


class RiskDashboardSerializer(serializers.Serializer):
    """风险仪表盘数据"""
    
    # 组合统计
    total_portfolios = serializers.IntegerField()
    active_portfolios = serializers.IntegerField()
    
    # 今日交易
    today_trades = serializers.IntegerField()
    today_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    
    # 风险预警
    pending_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    
    # 收益统计
    total_return = serializers.DecimalField(max_digits=10, decimal_places=4)
    avg_sharpe_ratio = serializers.DecimalField(max_digits=10, decimal_places=4)


class RiskThresholdSerializer(serializers.Serializer):
    """风险阈值配置"""
    
    indicator_name = serializers.CharField()
    threshold_type = serializers.ChoiceField(choices=['max', 'min'])
    threshold_value = serializers.DecimalField(max_digits=18, decimal_places=4)
    severity = serializers.ChoiceField(choices=RiskAlert.SEVERITY_CHOICES)
    description = serializers.CharField()
