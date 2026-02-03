from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'name': 'Risk Management System API',
        'version': '1.0.0',
        'endpoints': {
            'accounts': '/api/accounts/',
            'risk': '/api/risk/',
            'tasks': '/api/tasks/',
            'token': '/api/token/',
            'token_refresh': '/api/token/refresh/',
            'token_verify': '/api/token/verify/',
        },
        'documentation': 'Visit /api-auth/ for DRF browsable API',
    })

urlpatterns = [
    # API 根路径
    path('', api_root, name='api-root'),
    
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
