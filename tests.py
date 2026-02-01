"""
风险预警系统 - 单元测试
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, Role, Permission


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'phone': '13800138000',
            'department': '投资部',
            'position': '投资经理'
        }
    
    def test_create_user(self):
        """测试创建用户"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """测试创建超级用户"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_email_required(self):
        """测试邮箱必填"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='test123')
    
    def test_get_role_names(self):
        """测试获取角色名称"""
        user = User.objects.create_user(**self.user_data)
        role = Role.objects.create(name='测试角色', code='test')
        user.roles.add(role)
        self.assertIn('测试角色', user.get_role_names())


class RoleModelTest(TestCase):
    """角色模型测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.role = Role.objects.create(
            name='管理员',
            code='admin',
            description='系统管理员'
        )
    
    def test_role_str(self):
        """测试角色字符串表示"""
        self.assertEqual(str(self.role), '管理员')
    
    def test_role_unique_code(self):
        """测试角色代码唯一"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Role.objects.create(name='管理员2', code='admin')


class PortfolioAPITest(APITestCase):
    """组合API测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_portfolios(self):
        """测试获取组合列表"""
        url = reverse('portfolio-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_portfolio(self):
        """测试创建组合"""
        url = reverse('portfolio-list')
        data = {
            'code': 'TEST001',
            'name': '测试组合',
            'portfolio_type': 'mixed',
            'manager': '测试经理',
            'asset_scale': 1000000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'TEST001')
    
    def test_retrieve_portfolio(self):
        """测试获取单个组合"""
        from risk.models import Portfolio
        portfolio = Portfolio.objects.create(
            code='TEST002',
            name='测试组合2',
            portfolio_type='stock'
        )
        url = reverse('portfolio-detail', args=[portfolio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RiskIndicatorAPITest(APITestCase):
    """风险指标API测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
        from risk.models import Portfolio
        self.portfolio = Portfolio.objects.create(
            code='TEST003',
            name='测试组合3',
            portfolio_type='mixed'
        )
    
    def test_list_indicators(self):
        """测试获取指标列表"""
        url = reverse('indicator-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_latest_indicators(self):
        """测试获取最新指标"""
        url = reverse('indicator-latest')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TradeAPITest(APITestCase):
    """交易API测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
        from risk.models import Portfolio
        self.portfolio = Portfolio.objects.create(
            code='TEST004',
            name='测试组合4',
            portfolio_type='stock'
        )
    
    def test_list_trades(self):
        """测试获取交易列表"""
        url = reverse('trade-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_trade_summary(self):
        """测试获取交易统计"""
        url = reverse('trade-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_abnormal_trades(self):
        """测试获取异常交易"""
        url = reverse('trade-abnormal')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AlertAPITest(APITestCase):
    """预警API测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_alerts(self):
        """测试获取预警列表"""
        url = reverse('alert-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_pending_alerts(self):
        """测试获取待处理预警"""
        url = reverse('alert-pending')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_alert_statistics(self):
        """测试获取预警统计"""
        url = reverse('alert-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardAPITest(APITestCase):
    """仪表盘API测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_dashboard(self):
        """测试获取仪表盘数据"""
        url = reverse('risk-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_portfolios', response.data)
        self.assertIn('pending_alerts', response.data)


class AuthenticationTest(APITestCase):
    """认证测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
    
    def test_login(self):
        """测试登录"""
        url = reverse('login')
        data = {
            'email': 'admin@example.com',
            'password': 'admin123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_logout(self):
        """测试登出"""
        # 先登录获取token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        url = reverse('logout')
        data = {'refresh': str(refresh)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
