from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # JWT认证
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # 应用路由
    path('api/accounts/', include('accounts.urls')),
    path('api/risk/', include('risk.urls')),
    path('api/tasks/', include('tasks.urls')),
    
    # DRF可浏览API
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
