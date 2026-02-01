from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """只有超级管理员才能访问"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """管理员可读写，其他人只能读取"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_superuser or request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_superuser or request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """对象所有者可编辑，其他人只能读取"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user


class HasPermission(permissions.BasePermission):
    """检查用户是否有指定权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 超级用户拥有所有权限
        if request.user.is_superuser:
            return True
        
        # 检查用户是否拥有该权限
        permission_code = view.permission_code
        if not permission_code:
            return True
        
        return request.user.roles.filter(
            permissions__code=permission_code
        ).exists()
