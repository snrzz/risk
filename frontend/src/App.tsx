import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Menu, message } from 'antd'
import {
  DashboardOutlined,
  BankOutlined,
  LineChartOutlined,
  SwapOutlined,
  AlertOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined
} from '@ant-design/icons'

import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import RiskIndicator from './pages/RiskIndicator'
import Trade from './pages/Trade'
import Alert from './pages/Alert'
import Login from './pages/Login'
import { authService } from './services/api'

const { Header, Sider, Content } = Layout

const App: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    setIsAuthenticated(!!token)
  }, [])

  const handleLogout = () => {
    authService.logout()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    message.success('退出成功')
    setIsAuthenticated(false)
  }

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/portfolio', icon: <BankOutlined />, label: '组合管理' },
    { key: '/risk', icon: <LineChartOutlined />, label: '风险指标' },
    { key: '/trade', icon: <SwapOutlined />, label: '交易监控' },
    { key: '/alert', icon: <AlertOutlined />, label: '风险预警' },
  ]

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />
  }

  return (
    <Layout className="site-layout">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div className="logo">
          {collapsed ? '风险' : '风险预警系统'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['/']}
          items={menuItems}
          onClick={({ key }) => {
            window.location.href = key
          }}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 16, fontWeight: 'bold' }}>保险资产管理风险预警系统</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <UserOutlined />
            <span>管理员</span>
            <LogoutOutlined onClick={handleLogout} style={{ cursor: 'pointer' }} />
          </div>
        </Header>
        <Content style={{ margin: '16px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/risk" element={<RiskIndicator />} />
            <Route path="/trade" element={<Trade />} />
            <Route path="/alert" element={<Alert />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
