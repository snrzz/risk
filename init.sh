#!/bin/bash

echo "========================================="
echo "风险预警系统 - 初始化脚本"
echo "========================================="

# 检查Python版本
echo "检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo ""
echo "安装Python依赖..."
pip install -r requirements.txt -q

# 数据库迁移
echo ""
echo "执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
echo ""
echo "创建管理员账户..."
python manage.py shell -c "
from accounts.models import User, Role
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'admin123')
    print('管理员账户已创建: admin@example.com / admin123')
else:
    print('管理员账户已存在')
"

# 预置权限数据
echo ""
echo "初始化权限数据..."
python manage.py shell -c "
from accounts.models import Permission, Role

# 创建权限
permissions_data = [
    ('用户管理', 'user_manage', 'user', 'manage'),
    ('角色管理', 'role_manage', 'role', 'manage'),
    ('组合管理', 'portfolio_manage', 'portfolio', 'manage'),
    ('交易查看', 'trade_read', 'trade', 'read'),
    ('风险查看', 'risk_read', 'risk', 'read'),
    ('预警处理', 'alert_manage', 'alert', 'manage'),
    ('任务管理', 'task_manage', 'task', 'manage'),
]

for name, code, resource, action in permissions_data:
    Permission.objects.get_or_create(code=code, defaults={
        'name': name,
        'resource_type': resource,
        'action_type': action,
        'description': f'{name}权限'
    })

print('权限数据初始化完成')
"

# 预置角色
echo ""
echo "初始化角色..."
python manage.py shell -c "
from accounts.models import Role, Permission

admin_perms = Permission.objects.all()
admin_role, _ = Role.objects.get_or_create(code='admin', defaults={
    'name': '管理员',
    'description': '系统管理员'
})
admin_role.permissions.set(admin_perms)
admin_role.save()

risk_perms = Permission.objects.filter(code__in=['portfolio_manage', 'trade_read', 'risk_read', 'alert_manage'])
risk_role, _ = Role.objects.get_or_create(code='risk_manager', defaults={
    'name': '风控经理',
    'description': '风险管理人员'
})
risk_role.permissions.set(risk_perms)
risk_role.save()

print('角色数据初始化完成')
"

echo ""
echo "========================================="
echo "初始化完成！"
echo "========================================="
echo ""
echo "启动服务: python manage.py runserver 0.0.0.0:8000"
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/api/docs/"
echo ""
echo "管理员账户: admin@example.com / admin123"
echo ""
