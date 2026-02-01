import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/index.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/alerts/index.vue'),
    meta: { title: '告警中心' }
  },
  {
    path: '/metrics',
    name: 'Metrics',
    component: () => import('@/views/metrics/index.vue'),
    meta: { title: '监控指标' }
  },
  {
    path: '/datasources',
    name: 'Datasources',
    component: () => import('@/views/datasources/index.vue'),
    meta: { title: '数据源配置' }
  },
  {
    path: '/rules',
    name: 'Rules',
    component: () => import('@/views/rules/index.vue'),
    meta: { title: '告警规则' }
  },
  {
    path: '/notify',
    name: 'Notify',
    component: () => import('@/views/notify/index.vue'),
    meta: { title: '通知渠道' }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/reports/index.vue'),
    meta: { title: '报告管理' }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/index.vue'),
    meta: { title: '系统管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
