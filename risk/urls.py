from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioViewSet, RiskIndicatorViewSet, TradeViewSet,
    HoldingViewSet, RiskAlertViewSet, RiskDashboardView
)

router = DefaultRouter()
router.register(r'portfolios', PortfolioViewSet, basename='portfolio')
router.register(r'indicators', RiskIndicatorViewSet, basename='indicator')
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'holdings', HoldingViewSet, basename='holding')
router.register(r'alerts', RiskAlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', RiskDashboardView.as_view(), name='risk-dashboard'),
]
