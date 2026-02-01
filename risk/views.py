from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Max, Q
from django.utils import timezone
from datetime import timedelta
from .models import Portfolio, RiskIndicator, Trade, Holding, RiskAlert
from .serializers import (
    PortfolioSerializer, RiskIndicatorSerializer, TradeSerializer,
    HoldingSerializer, RiskAlertSerializer, RiskAlertUpdateSerializer,
    RiskDashboardSerializer
)
from accounts.permissions import IsAdminOrReadOnly


class PortfolioViewSet(viewsets.ModelViewSet):
    """组合视图集"""
    
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选条件
        status = self.request.query_params.get('status')
        portfolio_type = self.request.query_params.get('type')
        search = self.request.query_params.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if portfolio_type:
            queryset = queryset.filter(portfolio_type=portfolio_type)
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(manager__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def risk_summary(self, request, pk=None):
        """获取组合风险汇总"""
        portfolio = self.get_object()
        
        # 最新风险指标
        latest_indicator = RiskIndicator.objects.filter(
            portfolio=portfolio
        ).order_by('-indicator_date').first()
        
        # 今日交易
        today = timezone.now().date()
        today_trades = Trade.objects.filter(
            portfolio=portfolio,
            trade_date=today
        ).aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )
        
        # 活跃预警
        pending_alerts = RiskAlert.objects.filter(
            portfolio=portfolio,
            status='pending'
        ).count()
        
        return Response({
            'portfolio': PortfolioSerializer(portfolio).data,
            'latest_indicator': RiskIndicatorSerializer(latest_indicator).data if latest_indicator else None,
            'today_trades': today_trades,
            'pending_alerts': pending_alerts
        })


class RiskIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    """风险指标视图集（只读）"""
    
    queryset = RiskIndicator.objects.all()
    serializer_class = RiskIndicatorSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        portfolio_id = self.request.query_params.get('portfolio')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        if start_date:
            queryset = queryset.filter(indicator_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(indicator_date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取所有组合最新风险指标"""
        from django.db.models import Subquery, OuterRef
        
        # 子查询：每个组合最新指标
        latest_ids = RiskIndicator.objects.filter(
            portfolio=OuterRef('portfolio')
        ).order_by('-indicator_date').values('id')[:1]
        
        indicators = RiskIndicator.objects.filter(
            id__in=Subquery(latest_ids)
        ).select_related('portfolio')
        
        serializer = self.get_serializer(indicators, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """获取组合历史风险指标"""
        portfolio_id = request.query_params.get('portfolio')
        if not portfolio_id:
            return Response(
                {'error': '请指定组合ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        indicators = RiskIndicator.objects.filter(
            portfolio_id=portfolio_id
        ).order_by('indicator_date')
        
        serializer = self.get_serializer(indicators, many=True)
        return Response(serializer.data)


class TradeViewSet(viewsets.ModelViewSet):
    """交易记录视图集"""
    
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        portfolio_id = self.request.query_params.get('portfolio')
        trade_type = self.request.query_params.get('type')
        status = self.request.query_params.get('status')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        is_abnormal = self.request.query_params.get('is_abnormal')
        search = self.request.query_params.get('search')
        
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        if trade_type:
            queryset = queryset.filter(trade_type=trade_type)
        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(trade_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(trade_date__lte=end_date)
        if is_abnormal is not None:
            queryset = queryset.filter(is_abnormal=is_abnormal.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(security_code__icontains=search) |
                Q(security_name__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """交易统计汇总"""
        portfolio_id = request.query_params.get('portfolio')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        filters = Q()
        if portfolio_id:
            filters &= Q(portfolio_id=portfolio_id)
        if start_date:
            filters &= Q(trade_date__gte=start_date)
        if end_date:
            filters &= Q(trade_date__lte=end_date)
        
        summary = Trade.objects.filter(filters).aggregate(
            total_count=Count('id'),
            total_amount=Sum('amount'),
            buy_count=Count('id', filter=Q(trade_type='buy')),
            sell_count=Count('id', filter=Q(trade_type='sell')),
            abnormal_count=Count('id', filter=Q(is_abnormal=True))
        )
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def abnormal(self, request):
        """异常交易列表"""
        queryset = self.get_queryset().filter(is_abnormal=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class HoldingViewSet(viewsets.ReadOnlyModelViewSet):
    """持仓信息视图集（只读）"""
    
    queryset = Holding.objects.all()
    serializer_class = HoldingSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        portfolio_id = self.request.query_params.get('portfolio')
        holding_date = self.request.query_params.get('date')
        security_type = self.request.query_params.get('security_type')
        
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        if holding_date:
            queryset = queryset.filter(holding_date=holding_date)
        else:
            # 默认获取最新日期
            queryset = queryset.filter(
                holding_date=Holding.objects.filter(
                    portfolio=OuterRef('portfolio')
                ).order_by('-holding_date').values('holding_date')[:1]
            )
        if security_type:
            queryset = queryset.filter(security_type=security_type)
        
        return queryset


class RiskAlertViewSet(viewsets.ModelViewSet):
    """风险预警视图集"""
    
    queryset = RiskAlert.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return RiskAlertUpdateSerializer
        return RiskAlertSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        status = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        alert_type = self.request.query_params.get('type')
        portfolio_id = self.request.query_params.get('portfolio')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        if start_date:
            queryset = queryset.filter(alert_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(alert_time__date__lte=end_date)
        
        return queryset
    
    def perform_update(self, serializer):
        # 如果状态变为已确认/已解决/已忽略，记录处理人
        if serializer.validated_data.get('status') in ['acknowledged', 'resolved', 'ignored']:
            serializer.save(handled_by=self.request.user, handled_at=timezone.now())
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待处理预警"""
        queryset = self.get_queryset().filter(status='pending')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """预警统计"""
        from django.db.models import Count
        
        status_stats = RiskAlert.objects.values('status').annotate(
            count=Count('id')
        )
        severity_stats = RiskAlert.objects.values('severity').annotate(
            count=Count('id')
        )
        type_stats = RiskAlert.objects.values('alert_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'by_status': list(status_stats),
            'by_severity': list(severity_stats),
            'by_type': list(type_stats)
        })


class RiskDashboardView(views.APIView):
    """风险仪表盘"""
    
    def get(self, request):
        today = timezone.now().date()
        
        # 组合统计
        total_portfolios = Portfolio.objects.count()
        active_portfolios = Portfolio.objects.filter(status='active').count()
        
        # 今日交易
        today_trades = Trade.objects.filter(trade_date=today).aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )
        
        # 风险预警
        pending_alerts = RiskAlert.objects.filter(status='pending').count()
        critical_alerts = RiskAlert.objects.filter(
            status='pending',
            severity='critical'
        ).count()
        
        # 收益统计（所有组合最新指标）
        latest_indicators = RiskIndicator.objects.filter(
            id__in=RiskIndicator.objects.values('portfolio').annotate(
                latest_id=Max('id')
            ).values('latest_id')
        ).aggregate(
            avg_sharpe=Avg('sharpe_ratio'),
            total_return=Sum('cumulative_return')
        )
        
        data = {
            'total_portfolios': total_portfolios,
            'active_portfolios': active_portfolios,
            'today_trades': today_trades['count'] or 0,
            'today_amount': today_trades['amount'] or 0,
            'pending_alerts': pending_alerts,
            'critical_alerts': critical_alerts,
            'total_return': latest_indicators['total_return'] or 0,
            'avg_sharpe_ratio': latest_indicators['avg_sharpe'] or 0
        }
        
        serializer = RiskDashboardSerializer(data)
        return Response(serializer.data)
