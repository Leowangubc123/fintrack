<template>
  <div class="analysis-page">
    <!-- Tab 切换 -->
    <div class="analysis-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="analysis-tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 产品矩阵 -->
    <div v-show="activeTab === 'matrix'" class="tab-panel">
      <div class="card">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#007AFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            <span class="card-title">产品矩阵</span>
          </div>
          <div class="matrix-filter">
            <div class="filter-group">
              <span class="filter-label">时间范围:</span>
              <select v-model="matrixQuarter" class="filter-select">
                <option value="">第一季度</option>
                <option value="Q2">第二季度</option>
                <option value="Q3">第三季度</option>
                <option value="Q4">第四季度</option>
              </select>
              <select v-model="matrixMonth" class="filter-select">
                <option value="">全部月份</option>
                <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
              </select>
            </div>
            <div class="toggle-group">
              <button class="toggle-btn" :class="{ active: matrixView === 'amount' }" @click="matrixView = 'amount'">实际销量</button>
              <button class="toggle-btn" :class="{ active: matrixView === 'rate' }" @click="matrixView = 'rate'">完成率</button>
            </div>
          </div>
        </div>
        <div class="card-body" style="padding: 0;">
          <div class="matrix-table-wrapper">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th class="fixed-left-header" style="width: 160px;">营业部/成员</th>
                  <th v-for="p in matrixProducts" :key="p.id">{{ p.name }}</th>
                  <th class="fixed-right-header" style="width: 100px;">汇总</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="group in matrixGroups" :key="group.id">
                  <!-- 营业部行 -->
                  <tr class="group-row" @click="toggleGroup(group.id)">
                    <td class="fixed-left">
                      <span class="expand-icon">{{ expandedGroups.includes(group.id) ? '▼' : '▶' }}</span>
                      {{ group.name }} ({{ group.members?.length || 0 }}人)
                    </td>
                    <td v-for="(p, idx) in matrixProducts" :key="idx">
                      <span class="group-total">{{ getGroupProductTotal(group.id, p.id) }}万</span>
                    </td>
                    <td class="fixed-right">
                      <span class="group-total">{{ getGroupTotal(group.id) }}万</span>
                    </td>
                  </tr>
                  <!-- 成员行 -->
                  <tr
                    v-for="member in group.members"
                    v-show="expandedGroups.includes(group.id)"
                    :key="member.id"
                    class="member-row"
                  >
                    <td class="fixed-left" style="padding-left: 32px;">{{ member.name }}</td>
                    <td v-for="(p, idx) in matrixProducts" :key="idx">
                      <span
                        v-if="!hasMemberTask(member.id, p.id)"
                        class="no-task"
                      >无任务</span>
                      <span
                        v-else-if="matrixView === 'rate'"
                        class="rate-cell"
                        :class="getRateClass(getMemberProductRate(member.id, p.id))"
                      >
                        {{ getMemberProductRate(member.id, p.id) }}%
                      </span>
                      <span v-else class="rate-cell" :class="getRateClass(getMemberProductRate(member.id, p.id))">
                        {{ getMemberProductAmount(member.id, p.id) }}万
                      </span>
                    </td>
                    <td class="fixed-right">
                      <span
                        v-if="matrixView === 'rate'"
                        class="rate-cell"
                        :class="getRateClass(getMemberOverallRate(member.id))"
                      >
                        {{ getMemberOverallRate(member.id) }}%
                      </span>
                      <strong v-else>{{ getMemberTotal(member.id) }}万</strong>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <div class="info-tip">
            <span>💡</span>
            <span>提示: 点击营业部名称展开/折叠成员数据，左右两侧列固定，中间区域可横向滚动</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 个人查询 -->
    <div v-show="activeTab === 'personal'" class="tab-panel">
      <!-- 人员选择器 -->
      <div class="member-selector-bar">
        <select v-model="selectedGroupId" class="filter-select" style="width: 140px;" @change="onGroupChange">
          <option value="">选择营业部</option>
          <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
        </select>
        <select v-model="selectedMemberId" class="filter-select" style="width: 180px;" @change="onMemberChange">
          <option value="">选择成员</option>
          <option v-for="member in filteredMembers" :key="member.id" :value="member.id">{{ member.name }}</option>
        </select>
        <input type="text" v-model="memberSearch" class="search-input" placeholder="或输入姓名搜索...">
        <button class="btn btn-primary" @click="searchMember">查询</button>
      </div>

      <!-- 个人档案头部 -->
      <div v-if="selectedMember" class="profile-header">
        <div class="profile-card-main">
          <div class="profile-card-header-gradient">
            <div class="profile-avatar-large">{{ selectedMember.name?.charAt(0) || '?' }}</div>
            <div class="profile-basic-info">
              <div class="profile-name">{{ selectedMember.name }}</div>
              <div class="profile-department">{{ selectedMember.group_name || '' }}</div>
            </div>
            <div class="profile-completion">
              <div class="profile-completion-value">{{ memberStats.completion_rate }}%</div>
              <div class="profile-completion-label">综合完成率</div>
            </div>
          </div>
          <div class="profile-stats-row">
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">{{ memberStats.product_count }}个</div>
              <div class="profile-stat-label">参与任务数</div>
            </div>
            <div class="profile-stat-divider"></div>
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">¥{{ formatNumber(memberStats.total_sales) }}万</div>
              <div class="profile-stat-label">本年度销售额</div>
            </div>
            <div class="profile-stat-divider"></div>
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">¥{{ formatNumber(memberStats.avg_sales) }}万</div>
              <div class="profile-stat-label">平均每次任务销量</div>
            </div>
            <div class="profile-stat-divider"></div>
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">{{ memberStats.task_completion }}</div>
              <div class="profile-stat-label">任务完成次数</div>
            </div>
          </div>
        </div>
        <div class="profile-rank-card">
          <div class="rank-value">No.{{ memberStats.ranking }}</div>
          <div class="rank-label">辖区销量排名</div>
        </div>
      </div>

      <!-- 产品完成情况 + 热力图 -->
      <div v-if="selectedMember" class="two-col-layout">
        <div class="card" style="margin: 0;">
          <div class="card-header">
            <span class="card-title">产品完成情况明细</span>
            <div class="filter-group">
              <span class="filter-label">筛选:</span>
              <select v-model="personalMonthFilter" class="filter-select" @change="filterPersonalProducts">
                <option value="all">本年度全部</option>
                <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
              </select>
            </div>
          </div>
          <div class="card-body" style="padding: 0;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>产品名称</th>
                  <th>派发任务</th>
                  <th>实际完成</th>
                  <th>完成率</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="product in filteredPersonalProducts" :key="product.id">
                  <td><strong>{{ product.name }}</strong></td>
                  <td>
                    <span v-if="product.hasTask">¥{{ product.target }}万</span>
                    <span v-else class="no-task">无任务</span>
                  </td>
                  <td>
                    <span v-if="product.hasTask">¥{{ product.actual }}万</span>
                    <span v-else class="no-task">无任务</span>
                  </td>
                  <td>
                    <span v-if="product.hasTask" class="rate-cell" :class="getRateClass(product.rate)">{{ product.rate }}%</span>
                    <span v-else class="no-task">-</span>
                  </td>
                  <td>
                    <span v-if="product.hasTask" class="status-tag" :class="product.status">{{ product.statusText }}</span>
                    <span v-else class="no-task">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card" style="margin: 0;">
          <div class="card-header">
            <span class="card-title">月度销售热力图</span>
          </div>
          <div class="card-body">
            <div class="heatmap-grid">
              <div v-for="month in heatmapData" :key="month.month" class="heatmap-item">
                <div class="heatmap-month-label">{{ month.month }}月</div>
                <div
                  class="heatmap-cell"
                  :class="`level-${month.level}`"
                  :title="`${month.month}月: ¥${month.amount}万`"
                >
                  {{ month.amount > 0 ? month.amount : '-' }}
                </div>
              </div>
            </div>
            <div class="heatmap-legend">
              <span>销量:</span>
              <div class="legend-item">
                <div class="legend-color" style="background: #E5E5EA;"></div>
                <span>0</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #BBF7D0;"></div>
                <span>1-10万</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #86EFAC;"></div>
                <span>10-20万</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #4ADE80;"></div>
                <span>20-40万</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #16A34A;"></div>
                <span>40万+</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 销售趋势 -->
    <div v-show="activeTab === 'trends'" class="tab-panel">
      <div class="card">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#34C759" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            <span class="card-title">销售趋势分析</span>
          </div>
          <div class="trend-filter-group">
            <div class="toggle-group">
              <button class="toggle-btn" :class="{ active: trendTimeRange === 'month' }" @click="trendTimeRange = 'month'">本月</button>
              <button class="toggle-btn" :class="{ active: trendTimeRange === 'quarter' }" @click="trendTimeRange = 'quarter'">本季</button>
              <button class="toggle-btn" :class="{ active: trendTimeRange === 'year' }" @click="trendTimeRange = 'year'">本年</button>
            </div>
          </div>
        </div>
        <div class="card-body">
          <!-- KPI 卡片 -->
          <div class="trend-kpi-row">
            <div class="trend-kpi-card">
              <div class="trend-kpi-value">¥{{ formatNumber(trendStats.max_daily) }}万</div>
              <div class="trend-kpi-label">最高日销售额</div>
              <div class="trend-kpi-sub">{{ trendStats.max_daily_date || '-' }}</div>
            </div>
            <div class="trend-kpi-card">
              <div class="trend-kpi-value">¥{{ formatNumber(trendStats.avg_daily) }}万</div>
              <div class="trend-kpi-label">平均日销售额</div>
              <div class="trend-kpi-sub">本年度累计</div>
            </div>
            <div class="trend-kpi-card">
              <div class="trend-kpi-value" :class="trendStats.mom_growth >= 0 ? 'text-green' : 'text-red'">
                {{ trendStats.mom_growth >= 0 ? '↗' : '↘' }} {{ Math.abs(trendStats.mom_growth) }}%
              </div>
              <div class="trend-kpi-label">环比增长</div>
              <div class="trend-kpi-sub">较上月</div>
            </div>
          </div>

          <!-- 趋势图 -->
          <div class="trend-chart-section">
            <div class="chart-header">
              <span class="chart-title">销售额趋势（万元）</span>
              <div class="chart-toggle">
                <button class="chart-toggle-btn" :class="{ active: trendGroupBy === 'month' }" @click="trendGroupBy = 'month'; loadTrendData()">按月查看</button>
                <button class="chart-toggle-btn" :class="{ active: trendGroupBy === 'week' }" @click="trendGroupBy = 'week'; loadTrendData()">按周查看</button>
              </div>
            </div>
            <div class="trend-chart">
              <div v-for="(item, index) in trendChartData" :key="index" class="trend-chart-item">
                <div class="trend-bar-top-value" v-if="item.amount > 0">¥{{ formatNumber(item.amount) }}万</div>
                <div class="trend-bar-wrapper">
                  <div class="trend-bar" :style="{ height: item.amount > 0 ? Math.min((item.amount / Math.max(...trendChartData.map(d => d.amount))) * 120, 120) + 'px' : '0px' }"></div>
                </div>
                <div class="trend-bar-label">{{ item.label }}</div>
              </div>
              <div v-if="trendChartData.length === 0" class="chart-empty">暂无数据</div>
            </div>
          </div>

          <!-- 产品贡献度 -->
          <div class="contribution-section">
            <div class="chart-title">产品贡献度</div>
            <div class="contribution-list">
              <div v-for="(item, index) in productContribution.slice(0, 5)" :key="index" class="contribution-item">
                <div class="contribution-info">
                  <span class="contribution-name">{{ item.product_name }}</span>
                  <span class="contribution-percent">{{ item.percentage }}%</span>
                </div>
                <div class="contribution-bar-wrapper">
                  <div class="contribution-bar" :style="{ width: item.percentage + '%' }"></div>
                </div>
                <div class="contribution-amount">¥{{ formatNumber(item.amount) }}万</div>
              </div>
              <div v-if="productContribution.length === 0" class="chart-empty">暂无数据</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 营业部对比 -->
    <div v-show="activeTab === 'compare'" class="tab-panel">
      <!-- 营业部完成率趋势图 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#5856D6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
            <span class="card-title">营业部完成率趋势</span>
          </div>
          <div class="toggle-group">
            <button class="toggle-btn" :class="{ active: compareTimeRange === 'month' }" @click="compareTimeRange = 'month'; loadCompareData()">本月</button>
            <button class="toggle-btn" :class="{ active: compareTimeRange === 'quarter' }" @click="compareTimeRange = 'quarter'; loadCompareData()">本季</button>
            <button class="toggle-btn" :class="{ active: compareTimeRange === 'year' }" @click="compareTimeRange = 'year'; loadCompareData()">本年</button>
          </div>
        </div>
        <div class="card-body">
          <div class="group-trend-chart">
            <div v-for="(group, index) in sortedCompareGroups.slice(0, 6)" :key="group.id" class="group-trend-item">
              <div class="group-trend-name">{{ group.name }}</div>
              <div class="group-trend-line">
                <div v-for="(point, idx) in (groupTrendData[group.id]?.trend || [])" :key="idx" class="trend-point-wrapper">
                  <div class="trend-point" :class="point.completion_rate >= 100 ? 'success' : (point.completion_rate >= 50 ? 'warning' : 'danger')" :style="{ height: Math.min(point.completion_rate, 100) + '%' }"></div>
                  <div class="trend-point-label">{{ point.label?.split('月')[0]?.split('年')[1] || idx + 1 }}月</div>
                </div>
              </div>
              <div class="group-trend-current">{{ group.completion_rate }}%</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top: 20px;">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#5856D6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
            <span class="card-title">营业部业绩对比</span>
          </div>
        </div>
        <div class="card-body" style="padding: 0;">
          <table class="compare-table">
            <thead>
              <tr>
                <th style="width: 60px; text-align: center;">排名</th>
                <th>营业部</th>
                <th style="text-align: center;">成员数</th>
                <th style="text-align: right;">总销售</th>
                <th style="text-align: center;">完成率</th>
                <th style="text-align: right;">人均产能</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(group, index) in sortedCompareGroups" :key="group.id">
                <td style="text-align: center;">
                  <div class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
                </td>
                <td style="font-weight: 600; cursor: pointer; color: #007AFF;" @click="openGroupMembersModal(group)">{{ group.name }}</td>
                <td style="text-align: center;">{{ group.member_count || 0 }}</td>
                <td style="text-align: right; color: #007AFF; font-weight: 600;">¥{{ formatNumber(group.sales) }}万</td>
                <td style="text-align: center;">
                  <span class="rate-badge" :class="getRateClass(group.completion_rate)">{{ group.completion_rate }}%</span>
                </td>
                <td style="text-align: right;">¥{{ formatNumber(group.per_capita) }}万</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 完成率对比图 -->
      <div class="card" style="margin-top: 20px;">
        <div class="card-header">
          <span class="card-title">完成率对比</span>
        </div>
        <div class="card-body">
          <div class="completion-chart">
            <div v-for="(group, index) in sortedCompareGroups.slice(0, 6)" :key="group.id" class="completion-bar-item">
              <span class="completion-label">{{ group.name }}</span>
              <div class="completion-bar-wrapper">
                <div class="completion-bar-bg"></div>
                <div class="completion-bar" :style="{ width: Math.min(group.completion_rate, 100) + '%', background: getBarColor(group.completion_rate) }"></div>
                <div class="completion-bar-avg" :style="{ left: Math.min(avgCompletionRate, 100) + '%' }"></div>
              </div>
              <span class="completion-value">{{ group.completion_rate }}%</span>
            </div>
            <div v-if="sortedCompareGroups.length === 0" class="chart-empty">暂无数据</div>
          </div>
          <div v-if="sortedCompareGroups.length > 0" class="chart-legend">
            <div class="legend-item"><span class="legend-color" style="background: #34C759;"></span>完成率</div>
            <div class="legend-item"><span class="legend-line"></span>平均值({{ avgCompletionRate.toFixed(1) }}%)</div>
          </div>
        </div>
      </div>

      <!-- 营业部成员明细弹窗 -->
      <div v-if="groupMembersModalVisible" class="modal-overlay" @click="closeGroupMembersModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ selectedGroupForModal?.name }} - 成员明细</h3>
            <button class="modal-close" @click="closeGroupMembersModal">×</button>
          </div>
          <div class="modal-body">
            <table class="members-table">
              <thead>
                <tr>
                  <th style="text-align: center;">排名</th>
                  <th>成员姓名</th>
                  <th style="text-align: right;">目标</th>
                  <th style="text-align: right;">销售</th>
                  <th style="text-align: center;">完成率</th>
                  <th style="text-align: center;">记录数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(member, index) in groupMembersData" :key="member.id">
                  <td style="text-align: center;">{{ index + 1 }}</td>
                  <td>{{ member.name }}</td>
                  <td style="text-align: right;">¥{{ formatNumber(member.target) }}万</td>
                  <td style="text-align: right; color: #007AFF;">¥{{ formatNumber(member.sales) }}万</td>
                  <td style="text-align: center;">
                    <span class="rate-badge" :class="getRateClass(member.completion_rate)">{{ member.completion_rate }}%</span>
                  </td>
                  <td style="text-align: center;">{{ member.record_count }}</td>
                </tr>
                <tr v-if="groupMembersData.length === 0">
                  <td colspan="6" style="text-align: center; padding: 40px; color: #8E8E93;">暂无数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi, productsApi, membersApi, groupsApi, analysisApi } from '../api'

// Tab配置
const activeTab = ref('matrix')
const tabs = [
  { key: 'matrix', label: '产品矩阵' },
  { key: 'personal', label: '个人查询' },
  { key: 'trends', label: '销售趋势' },
  { key: 'compare', label: '营业部对比' }
]

// 数据
const products = ref([])
const groups = ref([])
const members = ref([])

// 产品矩阵
const matrixView = ref('amount')
const matrixQuarter = ref('')
const matrixMonth = ref('')
const matrixProducts = ref([])
const matrixGroups = ref([])
const expandedGroups = ref([])
const matrixSalesData = ref([]) // 存储销售数据
const matrixTargetData = ref([]) // 存储任务目标数据

// 个人查询
const selectedMemberId = ref('')
const selectedGroupId = ref('')
const memberSearch = ref('')
const selectedMember = ref(null)
const personalMonthFilter = ref('all')
const personalProducts = ref([])
const memberStats = ref({
  total_sales: 0,
  avg_sales: 0,
  completion_rate: 0,
  product_count: 0,
  task_completion: '0/0',
  ranking: 1,
  dept_avg_rate: 85.2
})
const heatmapData = ref([])

// 销售趋势
const trendProduct = ref('')
const trendTimeRange = ref('month')  // month, quarter, year - 用于筛选销售记录
const trendGroupBy = ref('month')    // month, week - 用于图表聚合
const trendStats = ref({
  max_daily: 0,
  max_daily_date: null,
  avg_daily: 0,
  yoy_growth: 0,      // 同比
  mom_growth: 0,      // 环比
  current_year_total: 0
})
const trendChartData = ref([])        // 趋势图数据
const productContribution = ref([])   // 产品贡献度数据

// 营业部对比
const compareGroups = ref([])
const compareTimeRange = ref('month') // month, quarter, year
const groupTrendData = ref({})        // 营业部趋势数据
const selectedGroupForModal = ref(null)
const groupMembersModalVisible = ref(false)
const groupMembersData = ref([])

onMounted(() => {
  loadData()
})

async function loadData() {
  try {
    // 加载基础数据
    const [productsRes, groupsRes, membersRes] = await Promise.all([
      productsApi.list(),
      groupsApi.list(),
      membersApi.list()
    ])
    products.value = productsRes
    groups.value = groupsRes
    members.value = membersRes

    // 加载分析数据
    const [matrixRes, comparisonRes, trendRes, trendStatRes, contributionRes] = await Promise.all([
      analysisApi.matrix(),
      analysisApi.groupComparison('month'),
      analysisApi.salesTrend({ year: new Date().getFullYear(), group_by: 'month' }),
      analysisApi.salesTrendStats({ year: new Date().getFullYear() }),
      analysisApi.productContribution(new Date().getFullYear())
    ])

    // 初始化产品矩阵数据
    matrixProducts.value = matrixRes.products.slice(0, 5)
    matrixGroups.value = matrixRes.groups.map(g => ({
      ...g,
      members: membersRes.filter(m => m.group_id === g.id)
    }))
    matrixSalesData.value = matrixRes.sales_data
    matrixTargetData.value = matrixRes.target_data || []
    console.log('[DEBUG] matrixTargetData:', matrixTargetData.value)
    console.log('[DEBUG] matrixSalesData:', matrixSalesData.value)
    expandedGroups.value = groupsRes.map(g => g.id)

    // 初始化个人查询数据
    if (groupsRes.length > 0) {
      selectedGroupId.value = groupsRes[0].id
    }

    // 初始化营业部对比数据（使用真实数据）
    compareGroups.value = comparisonRes

    // 初始化销售趋势数据
    trendChartData.value = trendRes
    trendStats.value = trendStatRes
    productContribution.value = contributionRes.contribution || []

    // 初始化热力图数据（使用真实月度趋势）
    heatmapData.value = trendRes

    // 加载营业部趋势数据
    const groupTrendRes = await analysisApi.groupTrend()
    groupTrendData.value = groupTrendRes

    // 初始化个人产品数据为空，选择成员后加载
    personalProducts.value = []
    memberStats.value = {
      total_sales: 0,
      avg_sales: 0,
      completion_rate: 0,
      product_count: 0,
      task_completion: '0/0',
      ranking: 1,
      dept_avg_rate: 85.2
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

// 加载成员详细数据
async function loadMemberDetail(memberId) {
  try {
    const [summaryRes, memberSalesRes, trendRes] = await Promise.all([
      analysisApi.memberSummary(memberId),
      analysisApi.memberSales({ member_id: memberId }),
      analysisApi.salesTrend({ year: new Date().getFullYear(), member_id: memberId }) // 加载该成员的月度销售趋势
    ])

    // 更新热力图数据（该成员的月度销售）
    heatmapData.value = trendRes

    // 从summaryRes获取任务目标
    const targetMap = {}
    const hasTaskMap = {}  // 标记哪些产品有任务分配
    if (summaryRes.targets) {
      summaryRes.targets.forEach(t => {
        targetMap[t.product_id] = t.target
        hasTaskMap[t.product_id] = true  // 有记录表示有任务分配
      })
    }

    // 计算全公司排名 - 获取所有成员的销售数据并排序
    let ranking = 1
    try {
      const allMemberSales = await analysisApi.memberSales()
      // 按成员ID汇总销售额
      const memberTotals = {}
      allMemberSales.forEach(sale => {
        if (!memberTotals[sale.member_id]) {
          memberTotals[sale.member_id] = 0
        }
        memberTotals[sale.member_id] += sale.total_amount
      })
      // 转换为数组并按销售额排序（从高到低）
      const sortedMembers = Object.entries(memberTotals)
        .map(([id, total]) => ({ member_id: parseInt(id), total_amount: total }))
        .sort((a, b) => b.total_amount - a.total_amount)
      // 找到当前成员的排名
      const memberRank = sortedMembers.findIndex(s => s.member_id === memberId)
      if (memberRank !== -1) {
        ranking = memberRank + 1
      }
    } catch (rankError) {
      console.error('计算排名失败:', rankError)
    }

    // 更新个人产品销售列表 - 显示所有产品，包括没有销售记录的产品
    // 从products.value获取所有产品，而不是仅从memberSalesRes
    const salesMap = {}
    memberSalesRes.forEach(sale => {
      salesMap[sale.product_id] = sale.total_amount
    })

    personalProducts.value = products.value.map(product => {
      const hasTask = hasTaskMap[product.id] || false
      const target = targetMap[product.id] || 0
      const actual = salesMap[product.id] || 0
      const rate = target > 0 ? Math.round((actual / target) * 100) : 0

      // 判断是否已结束募集但未完成
      const isExpired = product.status === '已结束'
      const isIncomplete = rate < 100
      const showIncomplete = isIncomplete && isExpired

      return {
        id: product.id,
        name: product.name || `产品${product.id}`,
        target: target,
        actual: actual,
        rate: rate,
        hasTask: hasTask,  // 标记是否有任务分配
        month: new Date().getMonth() + 1, // 使用当前月份
        status: rate >= 100 ? 'success' : (showIncomplete ? 'danger' : (rate >= 50 ? 'warning' : 'danger')),
        statusText: rate >= 100 ? '超额完成' : (showIncomplete ? '未完成' : (rate >= 50 ? '进行中' : '需努力'))
      }
    })

    // 更新成员统计
    // 计算任务完成次数：被分配任务的产品中，销量 >= 100% 的数量
    const completedTasks = personalProducts.value.filter(p => p.hasTask && p.rate >= 100).length
    const totalTasks = summaryRes.product_count || 0

    memberStats.value = {
      total_sales: summaryRes.total_sales,
      avg_sales: summaryRes.avg_sales,
      completion_rate: summaryRes.completion_rate || 0,
      product_count: summaryRes.product_count,
      task_completion: `${completedTasks}/${totalTasks}`,
      ranking: ranking,
      dept_avg_rate: 85.2
    }
  } catch (error) {
    console.error('加载成员详情失败:', error)
  }
}

// 计算属性
const avgCompletionRate = computed(() => {
  if (!compareGroups.value || compareGroups.value.length === 0) return 0
  const sum = compareGroups.value.reduce((acc, g) => acc + (g.completion_rate || 0), 0)
  return sum / compareGroups.value.length
})

const sortedCompareGroups = computed(() => {
  if (!compareGroups.value) return []
  return [...compareGroups.value].sort((a, b) => b.completion_rate - a.completion_rate)
})

const filteredMembers = computed(() => {
  if (!selectedGroupId.value) return members.value
  return members.value.filter(m => m.group_id === selectedGroupId.value)
})

const filteredPersonalProducts = computed(() => {
  if (personalMonthFilter.value === 'all') return personalProducts.value
  return personalProducts.value.filter(p => p.month === parseInt(personalMonthFilter.value))
})

// 方法
function toggleGroup(groupId) {
  const idx = expandedGroups.value.indexOf(groupId)
  if (idx > -1) {
    expandedGroups.value.splice(idx, 1)
  } else {
    expandedGroups.value.push(groupId)
  }
}

function onGroupChange() {
  selectedMemberId.value = ''
  selectedMember.value = null
}

async function onMemberChange() {
  selectedMember.value = members.value.find(m => m.id === selectedMemberId.value)
  if (selectedMember.value) {
    await loadMemberDetail(selectedMember.value.id)
  }
}

async function searchMember() {
  if (!memberSearch.value) return
  const found = members.value.find(m => m.name.includes(memberSearch.value))
  if (found) {
    selectedMemberId.value = found.id
    selectedGroupId.value = found.group_id
    selectedMember.value = found
    await loadMemberDetail(found.id)
  }
}

function filterPersonalProducts() {
  // 通过计算属性自动过滤
}

function getGroupProductTotal(groupId, productId) {
  // 从销售数据中汇总该营业部该产品的销售总额
  const groupMembers = members.value.filter(m => m.group_id === groupId).map(m => Number(m.id))
  const total = matrixSalesData.value
    .filter(s => groupMembers.includes(Number(s.member_id)) && Number(s.product_id) === Number(productId))
    .reduce((sum, s) => sum + Number(s.amount), 0)
  return total
}

function getGroupTotal(groupId) {
  // 从销售数据中汇总该营业部的销售总额
  const groupMembers = members.value.filter(m => m.group_id === groupId).map(m => Number(m.id))
  const total = matrixSalesData.value
    .filter(s => groupMembers.includes(Number(s.member_id)))
    .reduce((sum, s) => sum + Number(s.amount), 0)
  return total
}

function hasMemberTask(memberId, productId) {
  // 检查成员是否有该产品的任务分配
  const target = matrixTargetData.value.find(
    t => Number(t.member_id) === Number(memberId) && Number(t.product_id) === Number(productId)
  )
  // 如果在target_data中找到记录，说明有任务分配
  return !!target
}

function getMemberProductAmount(memberId, productId) {
  // 从销售数据中获取该成员该产品的销售金额（确保类型匹配）
  const sale = matrixSalesData.value.find(
    s => Number(s.member_id) === Number(memberId) && Number(s.product_id) === Number(productId)
  )
  return sale ? Number(sale.amount) : 0
}

function getMemberProductRate(memberId, productId) {
  // 计算该成员该产品的完成率（使用实际任务目标）
  const amount = getMemberProductAmount(memberId, productId)
  // 从任务目标数据中查找对应的目标金额（确保类型匹配）
  const target = matrixTargetData.value.find(
    t => Number(t.member_id) === Number(memberId) && Number(t.product_id) === Number(productId)
  )
  const targetAmount = target ? Number(target.target_amount) : 0

  // 调试信息
  console.log(`[DEBUG] 成员${memberId} 产品${productId}: 销量=${amount}, 目标=${targetAmount}`, target)

  // 如果没有任务目标，返回0；否则计算完成率（不限制最大值，显示真实完成率）
  if (targetAmount === 0) return 0
  return Math.round((amount / targetAmount) * 100)
}

function getMemberTotal(memberId) {
  // 从销售数据中汇总该成员的销售总额
  const total = matrixSalesData.value
    .filter(s => Number(s.member_id) === Number(memberId))
    .reduce((sum, s) => sum + Number(s.amount), 0)
  return total
}

function getMemberOverallRate(memberId) {
  // 计算该成员所有产品的整体完成率（只计算有任务分配的产品）
  let totalTarget = 0
  let totalAmount = 0

  matrixProducts.value.forEach(product => {
    // 只计算有任务分配的产品
    const target = matrixTargetData.value.find(
      t => Number(t.member_id) === Number(memberId) && Number(t.product_id) === Number(product.id)
    )
    if (target) {
      const amount = getMemberProductAmount(memberId, product.id)
      const targetAmount = Number(target.target_amount)
      totalAmount += amount
      totalTarget += targetAmount
    }
  })

  if (totalTarget === 0) return 0
  // 不限制最大值，显示真实完成率
  return Math.round((totalAmount / totalTarget) * 100)
}

function formatNumber(num) {
  if (!num) return '0'
  return Number(num).toLocaleString()
}

function getRateClass(rate) {
  if (rate >= 100) return 'rate-green'
  if (rate >= 80) return 'rate-yellow'
  if (rate >= 50) return 'rate-orange'
  return 'rate-red'
}

function getBarColor(rate) {
  if (rate >= 100) return '#34C759'
  if (rate >= 80) return '#FFCC00'
  if (rate >= 60) return '#FF9500'
  return '#FF3B30'
}

// 加载销售趋势数据
async function loadTrendData() {
  try {
    const year = new Date().getFullYear()
    const params = {
      year,
      group_by: trendGroupBy.value
    }
    if (trendProduct.value) {
      params.product_id = trendProduct.value
    }
    const [trendRes, trendStatRes, contributionRes] = await Promise.all([
      analysisApi.salesTrend(params),
      analysisApi.salesTrendStats({ year, product_id: trendProduct.value || undefined }),
      analysisApi.productContribution(year)
    ])
    trendChartData.value = trendRes
    trendStats.value = trendStatRes
    productContribution.value = contributionRes.contribution || []
  } catch (error) {
    console.error('加载销售趋势数据失败:', error)
  }
}

// 加载营业部对比数据
async function loadCompareData() {
  try {
    const [comparisonRes, groupTrendRes] = await Promise.all([
      analysisApi.groupComparison(compareTimeRange.value),
      analysisApi.groupTrend()
    ])
    compareGroups.value = comparisonRes
    groupTrendData.value = groupTrendRes
  } catch (error) {
    console.error('加载营业部对比数据失败:', error)
  }
}

// 打开营业部成员弹窗
async function openGroupMembersModal(group) {
  selectedGroupForModal.value = group
  try {
    const res = await analysisApi.groupMembers(group.id, compareTimeRange.value)
    groupMembersData.value = res.members || []
    groupMembersModalVisible.value = true
  } catch (error) {
    console.error('加载营业部成员数据失败:', error)
  }
}

// 关闭营业部成员弹窗
function closeGroupMembersModal() {
  groupMembersModalVisible.value = false
  selectedGroupForModal.value = null
  groupMembersData.value = []
}
</script>

<style scoped>
.analysis-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* Tab 切换 */
.analysis-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: #F5F5F7;
  border-radius: 10px;
  margin-bottom: 24px;
  width: fit-content;
}

.analysis-tab-btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background: transparent;
  color: #6E6E73;
  transition: all 0.2s ease;
}

.analysis-tab-btn:hover {
  color: #007AFF;
}

.analysis-tab-btn.active {
  background: #FFFFFF;
  color: #007AFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tab-panel {
  display: block;
}

/* 卡片样式 */
.card {
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 20px;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
}

.card-icon {
  width: 22px;
  height: 22px;
}

.card-body {
  padding: 24px;
}

/* 筛选器 */
.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-size: 13px;
  color: #6E6E73;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  background: #F5F5F7;
  color: #1D1D1F;
  cursor: pointer;
  outline: none;
}

.toggle-group {
  display: inline-flex;
  background: #FFFFFF;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.toggle-btn {
  padding: 8px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #6E6E73;
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background: #007AFF;
  color: white;
}

/* 产品矩阵 */
.matrix-filter {
  display: flex;
  align-items: center;
  gap: 16px;
}

.matrix-table-wrapper {
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.matrix-table th,
.matrix-table td {
  padding: 14px 18px;
  text-align: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  border-right: 1px solid rgba(0, 0, 0, 0.04);
  white-space: nowrap;
}

.matrix-table th:last-child,
.matrix-table td:last-child {
  border-right: none;
}

/* 产品列之间的分隔线 */
.matrix-table th:not(.fixed-left-header):not(.fixed-right-header),
.matrix-table td:not(.fixed-left):not(.fixed-right) {
  border-right: 1px solid rgba(0, 0, 0, 0.06);
}

/* 产品名称表头字体更大 */
.matrix-table th:not(.fixed-left-header):not(.fixed-right-header) {
  font-size: 16px;
  font-weight: 600;
}

/* 成员行字体更大，方便阅读 */
.member-row td {
  font-size: 15px;
  padding: 14px 18px;
}

/* 成员姓名列字体加大 */
.member-row .fixed-left {
  font-size: 15px;
  font-weight: 500;
}

/* 营业部行字体更大更粗 */
.group-row td {
  font-size: 15px;
  padding: 14px 18px;
}

/* 表头样式 - 更深的蓝色调，与个人数据区分 */
.matrix-table th {
  background: #007AFF;
  font-weight: 600;
  color: white;
  position: sticky;
  top: 0;
  z-index: 10;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.fixed-left-header {
  position: sticky;
  left: 0;
  z-index: 11;
  background: #007AFF;
  color: white;
}

.fixed-left {
  position: sticky;
  left: 0;
  background: white;
  z-index: 5;
  text-align: left;
}

.fixed-right-header {
  position: sticky;
  right: 0;
  z-index: 11;
  background: #007AFF;
  color: white;
}

.fixed-right {
  position: sticky;
  right: 0;
  background: #F0F8FF;
  z-index: 5;
  font-weight: 700;
  color: #007AFF;
}

/* 营业部行 - 深蓝色背景，与成员行明显区分 */
.group-row {
  background: #E8F4FD;
  cursor: pointer;
  font-weight: 600;
  border-left: 3px solid #007AFF;
}

.group-row:hover {
  background: #D1EBFC;
}

.group-row .fixed-left {
  background: #E8F4FD;
  font-weight: 700;
  color: #0056CC;
}

.group-row:hover .fixed-left {
  background: #D1EBFC;
}

.group-row .fixed-right {
  background: #E8F4FD;
}

.group-row:hover .fixed-right {
  background: #D1EBFC;
}

/* 成员行 - 浅色背景 */
.member-row {
  background: #FAFAFA;
}

.member-row:nth-child(even) {
  background: #F5F5F7;
}

.member-row:hover {
  background: #E8E8ED;
}

.member-row .fixed-left {
  background: inherit;
  color: #3A3A3C;
}

.expand-icon {
  display: inline-block;
  width: 16px;
  margin-right: 4px;
  text-align: center;
}

.group-total {
  color: #0056CC;
  font-weight: 700;
  font-size: 15px;
}

/* 产品列标题更醒目 */
.matrix-table th:not(.fixed-left-header):not(.fixed-right-header) {
  font-size: 14px;
  letter-spacing: 0.5px;
  min-width: 100px;
}

.rate-cell {
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  display: inline-block;
}

.rate-green { color: #059669; background: #D1FAE5; }
.rate-yellow { color: #D97706; background: #FEF3C7; }
.rate-orange { color: #EA580C; background: #FFE4D6; }
.rate-red { color: #DC2626; background: #FEE2E2; }

.info-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #E8F4FD;
  font-size: 13px;
  color: #0056CC;
  border-top: 1px solid #D1EBFC;
}

/* 个人查询 */
.member-selector-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: #F5F5F7;
  border-radius: 12px;
  align-items: center;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  width: 180px;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #007AFF;
  color: white;
}

.btn-primary:hover {
  background: #0056CC;
}

/* 个人档案 */
.profile-header {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.profile-card-main {
  flex: 1;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.profile-card-header-gradient {
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  color: white;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.profile-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.profile-basic-info {
  flex: 1;
}

.profile-name {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-department {
  font-size: 14px;
  opacity: 0.95;
  margin-bottom: 2px;
}

.profile-completion {
  text-align: center;
  padding-left: 16px;
  border-left: 1px solid rgba(255, 255, 255, 0.3);
}

.profile-completion-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-completion-label {
  font-size: 12px;
  opacity: 0.9;
}

.profile-stats-row {
  display: flex;
  padding: 24px;
  align-items: center;
  justify-content: space-around;
}

.profile-stat-item {
  text-align: center;
  flex: 1;
}

.profile-stat-value-large {
  font-size: 24px;
  font-weight: 700;
  color: #1D1D1F;
  margin-bottom: 6px;
}

.profile-stat-label {
  font-size: 13px;
  color: #6E6E73;
}

.profile-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(0, 0, 0, 0.1);
}

.profile-rank-card {
  width: 260px;
  background: white;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  text-align: center;
}

.rank-value {
  font-size: 44px;
  font-weight: 700;
  color: #007AFF;
  margin-bottom: 8px;
}

.rank-label {
  font-size: 14px;
  color: #6E6E73;
  margin-bottom: 12px;
}

.rank-dept-avg {
  font-size: 13px;
  color: #6E6E73;
}

.two-col-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* 数据表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  background: #F5F5F7;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #1D1D1F;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.data-table tr:hover {
  background: #FAFAFA;
}

.status-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.status-tag.success {
  background: #D1FAE5;
  color: #059669;
}

.status-tag.warning {
  background: #FEF3C7;
  color: #D97706;
}

.status-tag.danger {
  background: #FEE2E2;
  color: #DC2626;
}

.no-task {
  color: #8E8E93;
  font-style: italic;
}

/* 热力图 */
.heatmap-grid {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  align-items: stretch;
  min-height: 180px;
}

.heatmap-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.heatmap-month-label {
  font-size: 13px;
  color: #6E6E73;
  font-weight: 600;
}

.heatmap-cell {
  width: 100%;
  min-width: 36px;
  max-width: 60px;
  flex: 1;
  border-radius: 10px;
  background: #E5E5EA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: white;
  cursor: pointer;
  transition: transform 0.2s ease;
  min-height: 60px;
}

.heatmap-cell:hover {
  transform: scale(1.1);
}

.heatmap-cell.level-0 { background: #E5E5EA; color: #8E8E93; }
.heatmap-cell.level-1 { background: #BBF7D0; color: #059669; }
.heatmap-cell.level-2 { background: #86EFAC; color: #059669; }
.heatmap-cell.level-3 { background: #4ADE80; color: white; }
.heatmap-cell.level-4 { background: #16A34A; color: white; }

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  font-size: 13px;
  color: #6E6E73;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

/* 销售趋势 */
.trend-filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trend-kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.trend-kpi-card {
  background: #F5F5F7;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.trend-kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #1D1D1F;
  margin-bottom: 6px;
}

.trend-kpi-label {
  font-size: 14px;
  color: #6E6E73;
  margin-bottom: 4px;
}

.trend-kpi-sub {
  font-size: 12px;
  color: #8E8E93;
}

.text-green { color: #34C759; }
.text-red { color: #FF3B30; }

.chart-placeholder {
  height: 300px;
  background: #F5F5F7;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6E6E73;
  font-size: 14px;
}

/* 营业部对比 */
.compare-table {
  width: 100%;
  border-collapse: collapse;
}

.compare-table th {
  font-size: 13px;
  font-weight: 600;
  color: #6E6E73;
  background: #F5F5F7;
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.compare-table td {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 14px;
  color: #1D1D1F;
}

.compare-table tr:hover {
  background: #FAFAFA;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  background: #F5F5F7;
  color: #6E6E73;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%);
  color: white;
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
  color: white;
}

.rate-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.trend-arrow {
  font-size: 16px;
  font-weight: 700;
}

.trend-arrow.up {
  color: #34C759;
}

.trend-arrow.down {
  color: #FF3B30;
}

/* 完成率对比图 */
.completion-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.completion-bar-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.completion-label {
  width: 120px;
  font-size: 14px;
  color: #1D1D1F;
  font-weight: 500;
}

.completion-bar-wrapper {
  position: relative;
  flex: 1;
  height: 24px;
  background: #F5F5F7;
  border-radius: 12px;
  overflow: hidden;
}

.completion-bar {
  height: 100%;
  border-radius: 12px;
  transition: width 0.5s ease;
}

.completion-value {
  width: 60px;
  text-align: right;
  font-weight: 600;
  color: #1D1D1F;
}

/* 趋势图样式 */
.trend-chart-section {
  margin: 24px 0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.chart-toggle {
  display: flex;
  gap: 8px;
}

.chart-toggle-btn {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid #E5E5EA;
  background: #FFFFFF;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.chart-toggle-btn:hover {
  border-color: #007AFF;
  color: #007AFF;
}

.chart-toggle-btn.active {
  background: #007AFF;
  color: #FFFFFF;
  border-color: #007AFF;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 220px;
  padding: 16px;
  background: #FAFAFA;
  border-radius: 12px;
  gap: 12px;
  overflow-x: auto;
  padding-top: 30px;
}

.trend-chart-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 60px;
  flex: 1;
}

.trend-bar-wrapper {
  display: flex;
  align-items: flex-end;
  height: 120px;
  width: 100%;
  justify-content: center;
}

.trend-bar {
  width: 32px;
  background: linear-gradient(180deg, #34C759 0%, #28A745 100%);
  border-radius: 6px 6px 0 0;
  transition: height 0.3s ease;
}

.trend-bar-top-value {
  font-size: 11px;
  color: #007AFF;
  font-weight: 600;
  margin-bottom: 6px;
  white-space: nowrap;
  text-align: center;
}

.trend-bar-label {
  margin-top: 8px;
  font-size: 12px;
  color: #6E6E73;
}

.trend-bar-value {
  margin-top: 4px;
  font-size: 11px;
  color: #007AFF;
  font-weight: 600;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: #8E8E93;
  font-size: 14px;
}

/* 产品贡献度样式 */
.contribution-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #F0F0F0;
}

.contribution-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contribution-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.contribution-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.contribution-name {
  font-size: 14px;
  color: #1D1D1F;
  font-weight: 500;
}

.contribution-percent {
  font-size: 14px;
  color: #007AFF;
  font-weight: 600;
}

.contribution-bar-wrapper {
  height: 8px;
  background: #F5F5F7;
  border-radius: 4px;
  overflow: hidden;
}

.contribution-bar {
  height: 100%;
  background: linear-gradient(90deg, #007AFF 0%, #5856D6 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.contribution-amount {
  font-size: 12px;
  color: #6E6E73;
}

/* 营业部趋势图样式 */
.group-trend-chart {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.group-trend-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.group-trend-name {
  width: 100px;
  font-size: 14px;
  color: #1D1D1F;
  font-weight: 500;
  flex-shrink: 0;
}

.group-trend-line {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 60px;
  padding: 8px;
  background: #FAFAFA;
  border-radius: 8px;
}

.trend-point-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}

.trend-point {
  width: 100%;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
}

.trend-point.success {
  background: #34C759;
}

.trend-point.warning {
  background: #FFCC00;
}

.trend-point.danger {
  background: #FF3B30;
}

.trend-point-label {
  margin-top: 4px;
  font-size: 10px;
  color: #6E6E73;
}

.group-trend-current {
  width: 60px;
  text-align: right;
  font-weight: 700;
  color: #007AFF;
}

/* 完成率条形图增强样式 */
.completion-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #F5F5F7;
  border-radius: 12px;
}

.completion-bar-avg {
  position: absolute;
  top: -4px;
  bottom: -4px;
  width: 2px;
  background: #FF3B30;
  z-index: 2;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6E6E73;
}

.legend-color {
  width: 16px;
  height: 8px;
  border-radius: 4px;
}

.legend-line {
  width: 16px;
  height: 2px;
  background: #FF3B30;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #FFFFFF;
  border-radius: 16px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #F0F0F0;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #1D1D1F;
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #F5F5F7;
  font-size: 20px;
  color: #6E6E73;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #E5E5EA;
}

.modal-body {
  padding: 0;
  max-height: calc(80vh - 72px);
  overflow-y: auto;
}

.members-table {
  width: 100%;
  border-collapse: collapse;
}

.members-table th {
  padding: 16px;
  font-size: 13px;
  font-weight: 600;
  color: #6E6E73;
  border-bottom: 1px solid #F0F0F0;
  background: #FAFAFA;
}

.members-table td {
  padding: 16px;
  font-size: 14px;
  border-bottom: 1px solid #F5F5F7;
}

.text-muted {
  color: #8E8E93;
}

.text-green {
  color: #34C759;
}

.text-red {
  color: #FF3B30;
}

.rate-green {
  background: #D1FAE5;
  color: #059669;
}

.rate-yellow {
  background: #FEF3C7;
  color: #D97706;
}

.rate-orange {
  background: #FFE4D6;
  color: #EA580C;
}

.rate-red {
  background: #FEE2E2;
  color: #DC2626;
}
</style>
