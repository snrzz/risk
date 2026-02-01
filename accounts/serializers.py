from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Role, Permission

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'description', 'resource_type', 'action_type']


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        source='permissions'
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'permissions', 'permission_ids', 'created_at']
        read_only_fields = ['created_at']


class RoleSimpleSerializer(serializers.ModelSerializer):
    """简单角色序列化器"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'code']


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    roles = RoleSimpleSerializer(many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        write_only=True,
        source='roles'
    )
    role_names = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'department', 'position',
            'is_active', 'roles', 'role_ids', 'role_names',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_role_names(self, obj):
        return list(obj.roles.values_list('name', flat=True))


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'phone', 'department', 'position', 'role_ids'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': '两次密码不一致'
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role_ids = validated_data.pop('role_ids', [])
        user = User.objects.create_user(**validated_data)
        user.roles.set(role_ids)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """更新用户序列化器"""
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'department', 'position',
            'is_active', 'role_ids'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '两次新密码不一致'
            })
        return attrs


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    """Token响应序列化器"""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
