import axios from 'axios'

const API_BASE_URL = '/api'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理token过期
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
          refresh: refreshToken
        })
        
        const { access } = response.data
        localStorage.setItem('access_token', access)
        originalRequest.headers.Authorization = `Bearer ${access}`
        
        return api(originalRequest)
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export const authService = {
  login: async (email: string, password: string) => {
    const response = await api.post('/token/', { email, password })
    const { access, refresh, user } = response.data
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    return user
  },
  
  logout: async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      await api.post('/logout/', { refresh })
    } catch (error) {
      console.log('Logout error:', error)
    }
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/accounts/users/me/')
    return response.data
  },
  
  changePassword: async (oldPassword: string, newPassword: string) => {
    const response = await api.post('/accounts/users/1/change_password/', {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  }
}

export const portfolioService = {
  getAll: async (params?: Record<string, string>) => {
    const response = await api.get('/risk/portfolios/', { params })
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/risk/portfolios/${id}/`)
    return response.data
  },
  
  create: async (data: Record<string, unknown>) => {
    const response = await api.post('/risk/portfolios/', data)
    return response.data
  },
  
  update: async (id: number, data: Record<string, unknown>) => {
    const response = await api.put(`/risk/portfolios/${id}/`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/risk/portfolios/${id}/`)
    return response.data
  },
  
  getRiskSummary: async (id: number) => {
    const response = await api.get(`/risk/portfolios/${id}/risk_summary/`)
    return response.data
  }
}

export const riskIndicatorService = {
  getLatest: async () => {
    const response = await api.get('/risk/indicators/latest/')
    return response.data
  },
  
  getHistory: async (portfolioId: number) => {
    const response = await api.get('/risk/indicators/history/', {
      params: { portfolio: portfolioId }
    })
    return response.data
  },
  
  getAll: async (params?: Record<string, string>) => {
    const response = await api.get('/risk/indicators/', { params })
    return response.data
  }
}

export const tradeService = {
  getAll: async (params?: Record<string, string>) => {
    const response = await api.get('/risk/trades/', { params })
    return response.data
  },
  
  getSummary: async (params?: Record<string, string>) => {
    const response = await api.get('/risk/trades/summary/', { params })
    return response.data
  },
  
  getAbnormal: async () => {
    const response = await api.get('/risk/trades/abnormal/')
    return response.data
  }
}

export const alertService = {
  getAll: async (params?: Record<string, string>) => {
    const response = await api.get('/risk/alerts/', { params })
    return response.data
  },
  
  getPending: async () => {
    const response = await api.get('/risk/alerts/pending/')
    return response.data
  },
  
  getStatistics: async () => {
    const response = await api.get('/risk/alerts/statistics/')
    return response.data
  },
  
  updateStatus: async (id: number, status: string, comment?: string) => {
    const response = await api.patch(`/risk/alerts/${id}/`, {
      status,
      handle_comment: comment
    })
    return response.data
  }
}

export const dashboardService = {
  getData: async () => {
    const response = await api.get('/risk/dashboard/')
    return response.data
  }
}

export const taskService = {
  getAll: async () => {
    const response = await api.get('/tasks/')
    return response.data
  },
  
  execute: async (taskName: string) => {
    const response = await api.post('/tasks/execute/', { task_name: taskName })
    return response.data
  },
  
  getStatus: async (taskId: string) => {
    const response = await api.get('/tasks/status/', {
      params: { task_id: taskId }
    })
    return response.data
  }
}

export default api
