from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """自定义用户管理器"""
    
    def create_user(self, email, password=None, **extra_fields):
        """创建普通用户"""
        if not email:
            raise ValueError(_('邮箱地址必须提供'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('超级用户必须设置 is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('超级用户必须设置 is_superuser=True'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """自定义用户模型"""
    
    username = None  # 不使用用户名
    email = models.EmailField(_('邮箱地址'), unique=True)
    phone = models.CharField(_('手机号'), max_length=11, blank=True, null=True)
    department = models.CharField(_('部门'), max_length=100, blank=True, null=True)
    position = models.CharField(_('职位'), max_length=100, blank=True, null=True)
    roles = models.ManyToManyField('Role', verbose_name=_('角色'), blank=True)
    
    # 状态字段
    is_active = models.BooleanField(_('是否激活'), default=True)
    last_login = models.DateTimeField(_('最后登录时间'), blank=True, null=True)
    
    # 审计字段
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_role_names(self):
        """获取角色名称列表"""
        return list(self.roles.values_list('name', flat=True))


class Role(models.Model):
    """角色模型"""
    
    name = models.CharField(_('角色名称'), max_length=50, unique=True)
    code = models.CharField(_('角色代码'), max_length=50, unique=True)
    description = models.CharField(_('描述'), max_length=200, blank=True, null=True)
    permissions = models.ManyToManyField(
        'Permission',
        verbose_name=_('权限'),
        blank=True
    )
    
    # 审计字段
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('角色')
        verbose_name_plural = _('角色')
    
    def __str__(self):
        return self.name


class Permission(models.Model):
    """权限模型"""
    
    name = models.CharField(_('权限名称'), max_length=100)
    code = models.CharField(_('权限代码'), max_length=100, unique=True)
    description = models.CharField(_('描述'), max_length=200, blank=True, null=True)
    
    # 资源类型
    RESOURCE_TYPES = (
        ('user', '用户'),
        ('role', '角色'),
        ('permission', '权限'),
        ('portfolio', '组合'),
        ('trade', '交易'),
        ('risk', '风险'),
        ('report', '报告'),
        ('task', '任务'),
    )
    resource_type = models.CharField(
        _('资源类型'),
        max_length=20,
        choices=RESOURCE_TYPES,
        default='risk'
    )
    
    # 操作类型
    ACTION_TYPES = (
        ('create', '创建'),
        ('read', '读取'),
        ('update', '更新'),
        ('delete', '删除'),
        ('export', '导出'),
        ('execute', '执行'),
    )
    action_type = models.CharField(
        _('操作类型'),
        max_length=20,
        choices=ACTION_TYPES,
        default='read'
    )
    
    class Meta:
        verbose_name = _('权限')
        verbose_name_plural = _('权限')
    
    def __str__(self):
        return f"{self.name}({self.code})"
