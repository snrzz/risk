import request from './request'

// Dashboard API
export const dashboardApi = {
  getSummary: () => request.get('/dashboard/summary'),
  getRecentAlerts: (limit = 10) => request.get(`/dashboard/alerts/recent?limit=${limit}`),
  getAlertStats: (days = 7) => request.get(`/dashboard/alerts/stats?days=${days}`),
  getAlertTrend: (days = 7) => request.get(`/dashboard/charts/alert-trend?days=${days}`),
  getMetricStatus: () => request.get('/dashboard/charts/metric-status'),
  getSystemHealth: () => request.get('/dashboard/system/health')
}

// Alerts API
export const alertsApi = {
  getList: (params) => request.get('/alerts/', { params }),
  getStats: (days = 7) => request.get(`/alerts/stats?days=${days}`),
  getActive: (limit = 50) => request.get(`/alerts/active?limit=${limit}`),
  acknowledge: (data) => request.post('/alerts/acknowledge', data),
  resolve: (data) => request.post('/alerts/resolve', data)
}

// Metrics API
export const metricsApi = {
  getList: (params) => request.get('/metrics/', { params }),
  getDetail: (code) => request.get(`/metrics/${code}`),
  getData: (code, params) => request.get(`/metrics/${code}/data`, { params }),
  getRealtime: (codes) => request.get('/metrics/data/realtime', { params: { metric_codes: codes } }),
  getCategories: () => request.get('/metrics/categories')
}

// Datasources API
export const datasourcesApi = {
  getList: (params) => request.get('/datasources/', { params }),
  getDetail: (id) => request.get(`/datasources/${id}`),
  create: (data) => request.post('/datasources/', data),
  update: (id, data) => request.put(`/datasources/${id}`, data),
  delete: (id) => request.delete(`/datasources/${id}`),
  test: (id) => request.post(`/datasources/${id}/test`),
  sync: (id, syncType = 'incremental') => request.post(`/datasources/${id}/sync?sync_type=${syncType}`),
  getSyncLogs: (id, limit = 20) => request.get(`/datasources/${id}/sync-logs?limit=${limit}`),
  getTypes: () => request.get('/datasources/types')
}

// Rules API
export const rulesApi = {
  getList: (params) => request.get('/rules/', { params }),
  getDetail: (id) => request.get(`/rules/${id}`),
  create: (data) => request.post('/rules/', data),
  update: (id, data) => request.put(`/rules/${id}`, data),
  delete: (id) => request.delete(`/rules/${id}`),
  toggle: (id, enabled) => request.post(`/rules/${id}/toggle?enabled=${enabled}`),
  getTemplates: () => request.get('/rules/templates/list')
}

// Notify API
export const notifyApi = {
  getList: (params) => request.get('/notify/', { params }),
  getDetail: (id) => request.get(`/notify/${id}`),
  create: (data) => request.post('/notify/', data),
  update: (id, data) => request.put(`/notify/${id}`, data),
  delete: (id) => request.delete(`/notify/${id}`),
  test: (id) => request.post(`/notify/${id}/test`),
  send: (data) => request.post('/notify/send', data),
  getTypes: () => request.get('/notify/types/list')
}

// Reports API
export const reportsApi = {
  getTemplates: (params) => request.get('/reports/templates', { params }),
  getTemplate: (id) => request.get(`/reports/templates/${id}`),
  createTemplate: (data) => request.post('/reports/templates', data),
  updateTemplate: (id, data) => request.put(`/reports/templates/${id}`, data),
  deleteTemplate: (id) => request.delete(`/reports/templates/${id}`),
  getRecords: (params) => request.get('/reports/records', { params }),
  generate: (data) => request.post('/reports/generate', data),
  getRecord: (id) => request.get(`/reports/records/${id}`),
  getTypes: () => request.get('/reports/types')
}

// Admin API
export const adminApi = {
  getConfig: () => request.get('/admin/config'),
  updateConfig: (key, value, description) => request.put('/admin/config', { key, value, description }),
  getStats: () => request.get('/admin/stats'),
  getInfo: () => request.get('/admin/info'),
  healthCheck: () => request.get('/admin/health')
}
