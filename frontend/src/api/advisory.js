import api from './index'

export const advisoryApi = {
  // 获取投顾服务统计
  getStats: (params) => api.get('/advisory/stats', { params }),

  // 获取投顾订阅列表
  getSubscriptions: (params) => api.get('/advisory/subscriptions', { params }),

  // 导入投顾订阅数据
  importSubscriptions: (data) => api.post('/advisory/subscriptions/import', data),

  // 更新投顾订阅（转化信息）
  updateSubscription: (id, data) => api.put(`/advisory/subscriptions/${id}`, data),

  // 获取目标列表
  getTargets: (params) => api.get('/advisory/targets', { params }),

  // 保存目标
  saveTarget: (data) => api.post('/advisory/targets', data)
}
