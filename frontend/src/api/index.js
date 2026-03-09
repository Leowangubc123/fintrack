import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api

// 组织架构API
export const groupsApi = {
  list: () => api.get('/groups'),
  create: (data) => api.post('/groups', data),
  update: (id, data) => api.put(`/groups/${id}`, data),
  delete: (id) => api.delete(`/groups/${id}`)
}

export const membersApi = {
  list: (groupId) => api.get('/members', { params: { group_id: groupId } }),
  create: (data) => api.post('/members', data),
  update: (id, data) => api.put(`/members/${id}`, data),
  delete: (id) => api.delete(`/members/${id}`),
  transfer: (id, targetGroupId) => api.post(`/members/${id}/transfer`, null, {
    params: { target_group_id: targetGroupId }
  })
}

// 产品API
export const productsApi = {
  list: (params) => api.get('/products', { params }),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  archive: (id) => api.post(`/products/${id}/archive`)
}

// 导入API
export const importApi = {
  preview: (productId, file) => {
    const formData = new FormData()
    formData.append('product_id', productId)
    formData.append('file', file)
    return api.post('/import/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  execute: (data) => api.post('/import/execute', data)
}

// Dashboard API
export const dashboardApi = {
  summary: () => api.get('/dashboard/summary'),
  products: () => api.get('/dashboard/products'),
  groupsRanking: () => api.get('/dashboard/groups-ranking'),
  matrix: () => api.get('/dashboard/matrix'),
  largeOrders: (minAmount = 50) => api.get('/dashboard/large-orders', { params: { min_amount: minAmount } })
}