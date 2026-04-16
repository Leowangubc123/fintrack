import axios from 'axios'

// 根据环境选择 API 基础地址
const baseURL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api'

const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 如果是 FormData，删除 Content-Type 让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
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
    if (error.response) {
      console.error('Error status:', error.response.status)
      console.error('Error data:', error.response.data)
    }
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
  }),
  getAll: () => api.get('/members')
}

// 组织架构API（兼容命名）
export const organizationApi = {
  getMembers: () => api.get('/members')
}

// 产品API
export const productsApi = {
  list: (params) => api.get('/products', { params }),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  archive: (id) => api.post(`/products/${id}/archive`),
  unarchive: (id) => api.post(`/products/${id}/unarchive`),
  clearSales: (id) => api.post(`/products/${id}/clear-sales`),
  getGroupAssignments: (id) => api.get(`/products/${id}/assignments/groups`),
  saveGroupAssignments: (id, data) => api.post(`/products/${id}/assignments/groups`, data),
  getMemberAssignments: (id, groupId) => api.get(`/products/${id}/assignments/members`, { params: { group_id: groupId } }),
  saveMemberAssignments: (id, data) => api.post(`/products/${id}/assignments/members`, data)
}

// 导入API
export const importApi = {
  preview: (productId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    // 不设置 Content-Type，让浏览器自动设置正确的 boundary
    return api.post(`/import/preview?product_id=${productId}`, formData)
  },
  execute: (data) => api.post(`/import/execute?product_id=${data.product_id}`, data.records)
}

// Dashboard API
export const dashboardApi = {
  summary: () => api.get('/dashboard/summary'),
  products: () => api.get('/dashboard/products'),
  groupsRanking: (productId) => api.get('/dashboard/groups-ranking', { params: productId ? { product_id: productId } : {} }),
  matrix: () => api.get('/dashboard/matrix'),
  largeOrders: (minAmount = 50) => api.get('/dashboard/large-orders', { params: { min_amount: minAmount } })
}

// 数据分析API
export const analysisApi = {
  memberSales: (params) => api.get('/analysis/member-sales', { params }),
  groupSales: (params) => api.get('/analysis/group-sales', { params }),
  memberSummary: (memberId) => api.get(`/analysis/member-summary/${memberId}`),
  groupComparison: (timeRange) => api.get('/analysis/group-comparison', { params: { time_range: timeRange } }),
  groupTrend: () => api.get('/analysis/group-trend'),
  groupMembers: (groupId, timeRange) => api.get(`/analysis/group-members/${groupId}`, { params: { time_range: timeRange } }),
  salesTrend: (params) => api.get('/analysis/sales-trend', { params }),
  salesTrendStats: (params) => api.get('/analysis/sales-trend/stats', { params }),
  productContribution: (year) => api.get('/analysis/product-contribution', { params: { year } }),
  matrix: () => api.get('/analysis/matrix')
}

// 私募基金API
export const privateFundApi = {
  // 产品管理
  getProducts: () => api.get('/private-fund/products'),
  createProduct: (data) => api.post('/private-fund/products', data),
  updateProduct: (id, data) => api.put(`/private-fund/products/${id}`, data),
  deleteProduct: (id) => api.delete(`/private-fund/products/${id}`),

  // 交易记录
  createTransaction: (data) => api.post('/private-fund/transactions', data),
  deleteTransaction: (id) => api.delete(`/private-fund/transactions/${id}`),
  getRecentTransactions: (limit = 10) => api.get('/private-fund/transactions/recent', { params: { limit } }),

  // 年度统计
  getAnnualStats: (year) => api.get('/private-fund/stats/annual', { params: { year } }),
  getAnnualSales: (year) => api.get('/private-fund/sales/annual', { params: { year } }),

  // 保有统计 - 新版API
  getHoldings: (params) => api.get('/private-fund/holdings', { params }),
  getHoldingStats: () => api.get('/private-fund/holdings/stats'),
  uploadHoldings: (data, recordDate) => api.post(`/private-fund/holdings/upload?record_date=${recordDate}`, data),
  getHoldingDates: () => api.get('/private-fund/holdings/dates'),

  // 考核指标
  getTargets: (year) => api.get('/private-fund/targets', { params: { year } }),
  saveTarget: (data) => api.post('/private-fund/targets', data),

  // 保有统计 - 旧版API（兼容）
  getProductHoldings: () => api.get('/private-fund/holdings/products'),
  getGroupHoldings: () => api.get('/private-fund/holdings/groups'),
  getHoldingTrend: (period) => api.get('/private-fund/holdings/trend', { params: { period } })
}