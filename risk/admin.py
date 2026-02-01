from django.contrib import admin
from .models import Portfolio, RiskIndicator, Trade, Holding, RiskAlert


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'manager', 'portfolio_type', 'status', 'asset_scale']
    list_filter = ['status', 'portfolio_type', 'created_at']
    search_fields = ['code', 'name', 'manager']
    ordering = ['-created_at']


@admin.register(RiskIndicator)
class RiskIndicatorAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'indicator_date', 'daily_return', 'sharpe_ratio', 'max_drawdown']
    list_filter = ['indicator_date', 'portfolio__portfolio_type']
    search_fields = ['portfolio__code', 'portfolio__name']
    date_hierarchy = 'indicator_date'
    ordering = ['-indicator_date', '-created_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'trade_date', 'trade_type', 'security_code', 'security_name', 'quantity', 'amount', 'status', 'is_abnormal']
    list_filter = ['trade_date', 'trade_type', 'security_type', 'status', 'is_abnormal']
    search_fields = ['portfolio__code', 'security_code', 'security_name']
    date_hierarchy = 'trade_date'
    ordering = ['-trade_date', '-created_at']


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'holding_date', 'security_code', 'security_name', 'quantity', 'market_value', 'holding_ratio']
    list_filter = ['holding_date', 'security_type', 'portfolio__portfolio_type']
    search_fields = ['portfolio__code', 'security_code', 'security_name']
    date_hierarchy = 'holding_date'
    ordering = ['-holding_date', '-market_value']


@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'portfolio', 'status', 'alert_time', 'handled_by']
    list_filter = ['severity', 'status', 'alert_type', 'alert_time']
    search_fields = ['title', 'content', 'portfolio__code']
    date_hierarchy = 'alert_time'
    ordering = ['-alert_time']
    raw_id_fields = ['portfolio', 'handled_by']
