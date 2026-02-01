from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Role, Permission

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'phone', 'department', 'position', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['email', 'phone', 'department']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('个人信息', {'fields': ('phone', 'department', 'position')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'roles')}),
        ('时间', {'fields': ('created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password_confirm', 'phone', 'department', 'position', 'roles'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('roles')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'description', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']
    filter_horizontal = ['permissions']
    ordering = ['name']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'resource_type', 'action_type', 'description']
    list_filter = ['resource_type', 'action_type']
    search_fields = ['name', 'code']
    ordering = ['resource_type', 'action_type']
