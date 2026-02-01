from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from .models import User, Role, Permission
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    RoleSerializer, PermissionSerializer, LoginSerializer, ChangePasswordSerializer
)
from .permissions import IsSuperUser, IsAdminOrReadOnly


class LoginView(views.APIView):
    """用户登录"""
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': '邮箱或密码错误'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': '账户已被禁用'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 生成Token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class LogoutView(views.APIView):
    """用户登出"""
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': '登出成功'})
        except Exception as e:
            return Response({'message': '登出成功'})


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.prefetch_related('roles').all()
        
        # 筛选条件
        is_active = self.request.query_params.get('is_active')
        department = self.request.query_params.get('department')
        search = self.request.query_params.get('search')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if department:
            queryset = queryset.filter(department__icontains=department)
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) |
                models.Q(phone__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """修改密码"""
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': '原密码错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': '密码修改成功'})
    
    @action(detail=False, methods=['get'])
    def departments(self, request):
        """获取所有部门"""
        departments = User.objects.exclude(
            department__isnull=True
        ).exclude(
            department=''
        ).values_list('department', flat=True).distinct()
        
        return Response(list(departments))


class RoleViewSet(viewsets.ModelViewSet):
    """角色视图集"""
    
    queryset = Role.objects.prefetch_related('permissions').all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search)
            )
        return queryset


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """权限视图集（只读）"""
    
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按资源类型筛选
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def resource_types(self, request):
        """获取所有资源类型"""
        return Response(dict(Permission.RESOURCE_TYPES))
    
    @action(detail=False, methods=['get'])
    def action_types(self, request):
        """获取所有操作类型"""
        return Response(dict(Permission.ACTION_TYPES))
