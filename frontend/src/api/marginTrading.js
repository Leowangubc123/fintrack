import api from './index'

export const marginTradingApi = {
  // 获取统计数据
  getStats: (params) => api.get('/margin-trading/stats', { params }),

  // 获取个人余额
  getMemberBalances: (params) => api.get('/margin-trading/member-balances', { params }),

  // 获取营业部余额
  getGroupBalances: (params) => api.get('/margin-trading/group-balances', { params }),

  // 获取息费收入
  getIncome: (params) => api.get('/margin-trading/income', { params }),

  // 获取新开户
  getNewAccounts: (params) => api.get('/margin-trading/new-accounts', { params }),

  // 导入数据
  importData: (data) => api.post('/margin-trading/import', data),

  // 获取考核指标
  getTargets: (params) => api.get('/margin-trading/targets', { params }),

  // 保存考核指标
  saveTarget: (data) => api.post('/margin-trading/targets', data),

  // 删除指定周个人余额
  deleteMemberBalances: (record_week) => api.delete('/margin-trading/member-balances', { params: { record_week } }),

  // 删除指定周营业部余额
  deleteGroupBalances: (record_week) => api.delete('/margin-trading/group-balances', { params: { record_week } }),

  // 获取导入日志
  getImportLogs: (limit = 50) => api.get('/margin-trading/import-logs', { params: { limit } })
}
