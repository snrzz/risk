from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Portfolio(models.Model):
    """投资组合"""
    
    code = models.CharField(_('组合代码'), max_length=20, unique=True)
    name = models.CharField(_('组合名称'), max_length=200)
    manager = models.CharField(_('投资经理'), max_length=100, blank=True, null=True)
    
    # 组合类型
    PORTFOLIO_TYPES = (
        ('stock', '股票组合'),
        ('bond', '债券组合'),
        ('mixed', '混合组合'),
        ('index', '指数组合'),
        ('qdii', 'QDII组合'),
        ('other', '其他'),
    )
    portfolio_type = models.CharField(
        _('组合类型'),
        max_length=20,
        choices=PORTFOLIO_TYPES,
        default='mixed'
    )
    
    # 状态
    STATUS_CHOICES = (
        ('active', '运行中'),
        ('suspended', '暂停'),
        ('closed', '已关闭'),
    )
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # 资产规模
    asset_scale = models.DecimalField(
        _('资产规模(元)'),
        max_digits=18,
        decimal_places=2,
        default=0
    )
    
    # 备注
    remark = models.TextField(_('备注'), blank=True, null=True)
    
    # 创建时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('投资组合')
        verbose_name_plural = _('投资组合')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class RiskIndicator(models.Model):
    """风险指标"""
    
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        verbose_name=_('组合'),
        related_name='risk_indicators'
    )
    
    # 指标日期
    indicator_date = models.DateField(_('指标日期'))
    
    # 收益率指标
    daily_return = models.DecimalField(
        _('日收益率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    cumulative_return = models.DecimalField(
        _('累计收益率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    annualized_return = models.DecimalField(
        _('年化收益率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 风险指标
    daily_volatility = models.DecimalField(
        _('日波动率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    annualized_volatility = models.DecimalField(
        _('年化波动率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    max_drawdown = models.DecimalField(
        _('最大回撤'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    value_at_risk = models.DecimalField(
        _('VaR(95%)'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 风险调整收益
    sharpe_ratio = models.DecimalField(
        _('夏普比率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    sortino_ratio = models.DecimalField(
        _('索提诺比率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    information_ratio = models.DecimalField(
        _('信息比率'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 行业集中度
    industry_concentration = models.DecimalField(
        _('行业集中度'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    stock_concentration = models.DecimalField(
        _('个股集中度'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 持仓集中度
    top10_holdings_ratio = models.DecimalField(
        _('前十大持仓占比'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 创建时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('风险指标')
        verbose_name_plural = _('风险指标')
        unique_together = ['portfolio', 'indicator_date']
        ordering = ['-indicator_date', '-created_at']
    
    def __str__(self):
        return f"{self.portfolio.name} - {self.indicator_date}"


class Trade(models.Model):
    """交易记录"""
    
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        verbose_name=_('组合'),
        related_name='trades'
    )
    
    # 交易基本信息
    TRADE_TYPES = (
        ('buy', '买入'),
        ('sell', '卖出'),
    )
    trade_type = models.CharField(
        _('交易类型'),
        max_length=10,
        choices=TRADE_TYPES
    )
    
    SECURITY_TYPES = (
        ('stock', '股票'),
        ('bond', '债券'),
        ('fund', '基金'),
        ('derivative', '衍生品'),
        ('other', '其他'),
    )
    security_type = models.CharField(
        _('证券类型'),
        max_length=20,
        choices=SECURITY_TYPES
    )
    
    security_code = models.CharField(_('证券代码'), max_length=20)
    security_name = models.CharField(_('证券名称'), max_length=200)
    
    # 交易信息
    trade_date = models.DateField(_('交易日期'))
    trade_time = models.TimeField(_('交易时间'), blank=True, null=True)
    quantity = models.DecimalField(_('数量'), max_digits=18, decimal_places=2)
    price = models.DecimalField(_('成交价格'), max_digits=10, decimal_places=4)
    amount = models.DecimalField(_('成交金额'), max_digits=18, decimal_places=2)
    
    # 费率
    commission = models.DecimalField(_('佣金'), max_digits=18, decimal_places=2, default=0)
    stamp_tax = models.DecimalField(_('印花税'), max_digits=18, decimal_places=2, default=0)
    transfer_fee = models.DecimalField(_('过户费'), max_digits=18, decimal_places=2, default=0)
    
    # 交易状态
    STATUS_CHOICES = (
        ('pending', '待成交'),
        ('partial', '部分成交'),
        ('filled', '全部成交'),
        ('cancelled', '已取消'),
        ('rejected', '被拒绝'),
    )
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # 异常标记
    is_abnormal = models.BooleanField(_('是否异常'), default=False)
    abnormal_reason = models.TextField(_('异常原因'), blank=True, null=True)
    
    # 备注
    remark = models.TextField(_('备注'), blank=True, null=True)
    
    # 创建时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('交易记录')
        verbose_name_plural = _('交易记录')
        ordering = ['-trade_date', '-created_at']
    
    def __str__(self):
        return f"{self.portfolio.code} - {self.security_code} - {self.trade_type}"


class Holding(models.Model):
    """持仓信息"""
    
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        verbose_name=_('组合'),
        related_name='holdings'
    )
    
    # 持仓日期
    holding_date = models.DateField(_('持仓日期'))
    
    # 证券信息
    security_type = models.CharField(
        _('证券类型'),
        max_length=20,
        choices=Trade.SECURITY_TYPES
    )
    security_code = models.CharField(_('证券代码'), max_length=20)
    security_name = models.CharField(_('证券名称'), max_length=200)
    
    # 持仓信息
    quantity = models.DecimalField(_('持仓数量'), max_digits=18, decimal_places=2)
    cost = models.DecimalField(_('持仓成本'), max_digits=18, decimal_places=2)
    cost_price = models.DecimalField(_('持仓成本价'), max_digits=10, decimal_places=4)
    market_price = models.DecimalField(_('市价'), max_digits=10, decimal_places=4)
    market_value = models.DecimalField(_('市值'), max_digits=18, decimal_places=2)
    
    # 浮动盈亏
    unrealized_pnl = models.DecimalField(
        _('浮动盈亏'),
        max_digits=18,
        decimal_places=2,
        default=0
    )
    unrealized_pnl_ratio = models.DecimalField(
        _('浮动盈亏比例'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 持仓比例
    holding_ratio = models.DecimalField(
        _('持仓比例'),
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # 创建时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('持仓信息')
        verbose_name_plural = _('持仓信息')
        unique_together = ['portfolio', 'holding_date', 'security_code']
        ordering = ['-holding_date', '-market_value']
    
    def __str__(self):
        return f"{self.portfolio.code} - {self.security_code}"


class RiskAlert(models.Model):
    """风险预警"""
    
    # 预警类型
    ALERT_TYPES = (
        ('threshold', '阈值预警'),
        ('anomaly', '异常预警'),
        ('limit', '限制预警'),
        ('trend', '趋势预警'),
    )
    alert_type = models.CharField(
        _('预警类型'),
        max_length=20,
        choices=ALERT_TYPES
    )
    
    # 关联对象
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        verbose_name=_('组合'),
        related_name='alerts',
        blank=True,
        null=True
    )
    
    # 预警等级
    SEVERITY_CHOICES = (
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('critical', '严重'),
    )
    severity = models.CharField(
        _('预警等级'),
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='warning'
    )
    
    # 预警信息
    title = models.CharField(_('预警标题'), max_length=200)
    content = models.TextField(_('预警内容'))
    indicator_name = models.CharField(_('指标名称'), max_length=100, blank=True, null=True)
    indicator_value = models.DecimalField(
        _('指标值'),
        max_digits=18,
        decimal_places=4,
        blank=True,
        null=True
    )
    threshold = models.DecimalField(
        _('阈值'),
        max_digits=18,
        decimal_places=4,
        blank=True,
        null=True
    )
    
    # 预警状态
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
        ('ignored', '已忽略'),
    )
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # 处理信息
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name=_('处理人'),
        blank=True,
        null=True
    )
    handled_at = models.DateTimeField(_('处理时间'), blank=True, null=True)
    handle_comment = models.TextField(_('处理意见'), blank=True, null=True)
    
    # 通知信息
    notified = models.BooleanField(_('是否已通知'), default=False)
    notification_time = models.DateTimeField(_('通知时间'), blank=True, null=True)
    
    # 预警时间
    alert_time = models.DateTimeField(_('预警时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('风险预警')
        verbose_name_plural = _('风险预警')
        ordering = ['-alert_time']
    
    def __str__(self):
        return f"{self.title} - {self.severity}"
