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
                      <span class="group-total">{{ formatNumber(getGroupProductTotal(group.id, p.id)) }}万</span>
                    </td>
                    <td class="fixed-right">
                      <span class="group-total">{{ formatNumber(getGroupTotal(group.id)) }}万</span>
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
                        {{ formatNumber(getMemberProductAmount(member.id, p.id)) }}万
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
                      <strong v-else>{{ formatNumber(getMemberTotal(member.id)) }}万</strong>
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

    <!-- 年度经营看板 -->
    <div v-show="activeTab === 'dashboard'" class="tab-panel">
      <!-- 顶部控制栏 -->
      <div class="dashboard-controls">
        <div class="control-group">
          <span class="control-label">年份</span>
          <div class="toggle-group">
            <button v-for="y in yearOptions" :key="y" class="toggle-btn" :class="{ active: dashboardYear === y }" @click="setDashboardYear(y)">{{ y }}</button>
          </div>
        </div>
        <div class="control-group">
          <span class="control-label">季度</span>
          <div class="toggle-group">
            <button class="toggle-btn" :class="{ active: dashboardQuarter === 'all' }" @click="dashboardQuarter = 'all'">全年</button>
            <button class="toggle-btn" :class="{ active: dashboardQuarter === 'Q1' }" @click="dashboardQuarter = 'Q1'">Q1</button>
            <button class="toggle-btn" :class="{ active: dashboardQuarter === 'Q2' }" @click="dashboardQuarter = 'Q2'">Q2</button>
            <button class="toggle-btn" :class="{ active: dashboardQuarter === 'Q3' }" @click="dashboardQuarter = 'Q3'">Q3</button>
            <button class="toggle-btn" :class="{ active: dashboardQuarter === 'Q4' }" @click="dashboardQuarter = 'Q4'">Q4</button>
          </div>
        </div>
      </div>

      <!-- 产品发售甘特图 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#FF9500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            <span class="card-title">产品发售时间轴</span>
          </div>
          <div class="gantt-header-right">
            <span class="gantt-count-badge">{{ ganttProducts.length }} 个产品</span>
            <div class="gantt-legend">
              <span class="gantt-legend-item"><span class="gantt-legend-dot" style="background:#007AFF"></span>募集中</span>
              <span class="gantt-legend-item"><span class="gantt-legend-dot" style="background:#FF9500"></span>即将开始</span>
              <span class="gantt-legend-item"><span class="gantt-legend-dot" style="background:#8E8E93"></span>已结束</span>
            </div>
          </div>
        </div>
        <div class="card-body" style="padding: 0; overflow: hidden;">
          <div class="gantt-wrapper">
            <div class="gantt-header-row">
              <div class="gantt-name-col gantt-header-cell">产品名称</div>
              <div class="gantt-timeline-area gantt-header-cells">
                <div v-for="col in ganttColumns" :key="col.key" class="gantt-col-header" :style="{ width: col.widthPct + '%' }">{{ col.label }}</div>
              </div>
            </div>
            <div class="gantt-rows-wrapper">
              <div v-for="(product, idx) in ganttProducts" :key="product.id" class="gantt-row-item" :class="{ 'gantt-row-alt': idx % 2 === 1 }">
                <div class="gantt-name-col" :title="product.name">{{ product.name }}</div>
                <div class="gantt-timeline-area gantt-timeline-row">
                  <div v-for="col in ganttColumns" :key="col.key" class="gantt-grid-col" :style="{ width: col.widthPct + '%' }"></div>
                  <div
                    class="gantt-bar"
                    :style="getGanttBarStyle(product)"
                    :title="`${product.name}\n募集期：${product.start_date} → ${product.end_date}`"
                  >
                    <span class="gantt-bar-text">{{ product.name }}</span>
                  </div>
                </div>
              </div>
              <div v-if="ganttProducts.length === 0" class="gantt-empty">该时间段暂无产品发售</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 全年销量走势 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#34C759" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            <span class="card-title">全年销量走势</span>
          </div>
        </div>
        <div class="card-body" style="padding: 20px 24px 16px;">
          <!-- 年度总销售额大字 -->
          <div class="annual-total-hero">
            <div class="annual-total-label">{{ dashboardYear }} 年度总销售额</div>
            <div class="annual-total-value">¥ {{ formatNumber(dashboardYearTotal) }} <span class="annual-total-unit">万元</span></div>
          </div>
          <!-- SVG 图表 -->
          <div class="annual-svg-chart-container" ref="chartContainer">
            <svg class="annual-svg-chart" :viewBox="`0 0 780 220`" preserveAspectRatio="xMidYMid meet">
              <!-- 背景网格线 -->
              <line v-for="n in 4" :key="'grid'+n"
                :x1="48" :y1="20 + (n-1) * 42"
                :x2="768" :y2="20 + (n-1) * 42"
                stroke="#F0F0F0" stroke-width="1"/>
              <!-- Y轴标签 -->
              <text v-for="n in 4" :key="'ylabel'+n"
                :x="40" :y="20 + (n-1) * 42 + 4"
                text-anchor="end" font-size="10" fill="#AEAEB2">
                {{ formatNumber(chartYLabel(4 - n)) }}
              </text>
              <!-- 柱状图 -->
              <g v-for="(pt, i) in dashboardChartPoints" :key="'bar'+i">
                <rect
                  :x="48 + i * 60 + 12"
                  :y="pt.barH > 0 ? 20 + 126 - pt.barH : 146"
                  :width="36"
                  :height="pt.barH > 0 ? pt.barH : 0"
                  :fill="pt.barH > 0 ? 'url(#barGrad)' : '#E5E5EA'"
                  rx="4" ry="4"/>
                <!-- 数值标签 -->
                <text v-if="pt.amount > 0"
                  :x="48 + i * 60 + 30"
                  :y="pt.barH > 0 ? 20 + 126 - pt.barH - 5 : 140"
                  text-anchor="middle" font-size="10" font-weight="600" fill="#007AFF">
                  {{ formatNumber(pt.amount) }}
                </text>
                <!-- 月份标签 -->
                <text
                  :x="48 + i * 60 + 30"
                  y="170"
                  text-anchor="middle" font-size="12" font-weight="500" fill="#6E6E73">
                  {{ pt.month }}月
                </text>
              </g>
              <!-- 趋势折线 -->
              <polyline
                :points="trendPolylinePoints"
                fill="none" stroke="#FF9500" stroke-width="2.5"
                stroke-linejoin="round" stroke-linecap="round"
                stroke-dasharray="none"/>
              <!-- 趋势折线节点 -->
              <template v-for="(pt, i) in dashboardChartPoints" :key="'dot'+i">
                <circle v-if="pt.amount > 0"
                  :cx="48 + i * 60 + 30"
                  :cy="20 + 126 - pt.barH"
                  r="4" fill="#FF9500" stroke="white" stroke-width="2"/>
              </template>
              <!-- 渐变定义 -->
              <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#5AC8FA"/>
                  <stop offset="100%" stop-color="#007AFF"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <!-- 图例 -->
          <div class="annual-chart-legend" style="margin-top: 8px;">
            <span class="legend-bar-item"><span class="legend-bar-dot" style="background:linear-gradient(#5AC8FA,#007AFF)"></span>月销售额（万元）</span>
            <span class="legend-bar-item"><span class="legend-line-dot" style="background:#FF9500"></span>走势线</span>
          </div>
        </div>
      </div>

      <!-- 营业部战队排行 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title-section">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="#5856D6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span class="card-title">营业部排名</span>
          </div>
          <span class="ranking-subtitle">按全年总销售额排序 · 点击展开成员明细</span>
        </div>
        <div class="card-body" style="padding: 0;">
          <div v-if="dashboardGroups.length === 0" class="gantt-empty">暂无数据</div>
          <div class="team-ranking-list">
            <div v-for="(group, index) in dashboardGroups" :key="group.id" class="team-item">
              <div class="team-main-row" @click="toggleDashboardGroup(group.id)">
                <div class="team-rank-col">
                  <div class="rank-medal" :class="'medal-' + (index + 1)">{{ index + 1 }}</div>
                </div>
                <div class="team-name-col">{{ group.name }}</div>
                <div class="team-bar-col">
                  <div class="team-sales-track">
                    <div class="team-sales-fill" :style="{ width: (maxGroupSales > 0 ? group.sales / maxGroupSales * 100 : 0) + '%' }"></div>
                  </div>
                </div>
                <div class="team-sales-col">¥{{ formatNumber(group.sales) }}<span class="unit">万</span></div>
                <div class="team-percap-col">人均产能 <strong>¥{{ formatNumber(group.per_capita) }}</strong><span class="unit">万</span></div>
                <div class="team-expand-col">
                  <span class="expand-chevron" :class="{ open: expandedDashboardGroups.includes(group.id) }">›</span>
                </div>
              </div>
              <div v-if="expandedDashboardGroups.includes(group.id)" class="team-members-panel">
                <div v-if="!dashboardMembersData[group.id]" class="panel-loading">加载中...</div>
                <template v-else>
                  <div v-for="member in dashboardMembersData[group.id]" :key="member.id" class="member-contrib-row">
                    <span class="member-contrib-name">{{ member.name }}</span>
                    <div class="member-contrib-track">
                      <div class="member-contrib-fill" :style="{ width: getMemberPct(group.id, member) + '%' }"></div>
                    </div>
                    <span class="member-contrib-amount">¥{{ formatNumber(member.sales) }}万</span>
                    <span class="member-contrib-pct">{{ getMemberPct(group.id, member) }}%</span>
                  </div>
                  <div class="team-balance-row">
                    <span class="balance-label">均衡指数</span>
                    <span class="balance-tag" :class="getBalanceClass(group.id)">{{ getBalanceText(group.id) }}</span>
                    <span class="balance-hint">最高成员占比 {{ getTopMemberPct(group.id) }}%</span>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { productsApi, membersApi, groupsApi, analysisApi } from '../api'

// Tab配置
const activeTab = ref('matrix')
const tabs = [
  { key: 'matrix', label: '产品矩阵' },
  { key: 'dashboard', label: '年度看板' },
  { key: 'personal', label: '个人查询' }
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

// 年度经营看板
const dashboardYear = ref(new Date().getFullYear())
const dashboardQuarter = ref('all')
const dashboardCompareGroups = ref([])
const expandedDashboardGroups = ref([])
const dashboardMembersData = ref({})
const dashboardTrendData = ref([])

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
    const [matrixRes, trendRes, dashboardRes, dashTrendRes] = await Promise.all([
      analysisApi.matrix(),
      analysisApi.salesTrend({ year: new Date().getFullYear(), group_by: 'month' }),
      analysisApi.groupComparison('year'),
      analysisApi.salesTrend({ year: dashboardYear.value, group_by: 'month' })
    ])

    // 初始化产品矩阵数据
    matrixProducts.value = matrixRes.products.slice(0, 5)
    matrixGroups.value = matrixRes.groups.map(g => ({
      ...g,
      members: membersRes.filter(m => m.group_id === g.id)
    }))
    matrixSalesData.value = matrixRes.sales_data
    matrixTargetData.value = matrixRes.target_data || []
    expandedGroups.value = groupsRes.map(g => g.id)

    // 初始化个人查询数据
    if (groupsRes.length > 0) {
      selectedGroupId.value = groupsRes[0].id
    }

    // 初始化热力图数据（使用真实月度趋势）
    heatmapData.value = trendRes

    // 初始化年度看板数据
    dashboardCompareGroups.value = dashboardRes
    dashboardTrendData.value = dashTrendRes

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

// ── 年度看板计算属性 ──
const yearOptions = computed(() => {
  const y = new Date().getFullYear()
  return [y - 1, y, y + 1]
})

const ganttViewRange = computed(() => {
  const y = dashboardYear.value
  const map = {
    all: { start: new Date(y, 0, 1),  end: new Date(y, 11, 31) },
    Q1:  { start: new Date(y, 0, 1),  end: new Date(y, 2, 31)  },
    Q2:  { start: new Date(y, 3, 1),  end: new Date(y, 5, 30)  },
    Q3:  { start: new Date(y, 6, 1),  end: new Date(y, 8, 30)  },
    Q4:  { start: new Date(y, 9, 1),  end: new Date(y, 11, 31) },
  }
  return map[dashboardQuarter.value]
})

const ganttProducts = computed(() => {
  if (!products.value.length) return []
  const { start, end } = ganttViewRange.value
  return products.value
    .filter(p => {
      if (!p.start_date) return false
      const d = new Date(p.start_date)
      return d >= start && d <= end
    })
    .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
})

const ganttColumns = computed(() => {
  const { start } = ganttViewRange.value
  if (dashboardQuarter.value === 'all') {
    return Array.from({ length: 12 }, (_, i) => ({ key: i + 1, label: `${i + 1}月`, widthPct: 100 / 12 }))
  }
  const sm = start.getMonth()
  return Array.from({ length: 3 }, (_, i) => ({ key: sm + i + 1, label: `${sm + i + 1}月`, widthPct: 100 / 3 }))
})

const dashboardGroups = computed(() => {
  if (!dashboardCompareGroups.value.length) return []
  return [...dashboardCompareGroups.value].sort((a, b) => b.sales - a.sales)
})

const maxGroupSales = computed(() => {
  if (!dashboardGroups.value.length) return 1
  return Math.max(...dashboardGroups.value.map(g => g.sales)) || 1
})

const dashboardYearTotal = computed(() =>
  dashboardTrendData.value.reduce((s, d) => s + d.amount, 0)
)

const dashboardChartPoints = computed(() => {
  const maxAmt = Math.max(...dashboardTrendData.value.map(d => d.amount), 1)
  return Array.from({ length: 12 }, (_, i) => {
    const item = dashboardTrendData.value.find(d => d.month === i + 1)
    const amount = item?.amount || 0
    return { month: i + 1, amount, barPct: (amount / maxAmt) * 100, barH: Math.round((amount / maxAmt) * 126) }
  })
})

const trendPolylinePoints = computed(() => {
  return dashboardChartPoints.value
    .map((pt, i) => `${48 + i * 60 + 30},${pt.amount > 0 ? 20 + 126 - pt.barH : 146}`)
    .join(' ')
})

function chartYLabel(n) {
  const maxAmt = Math.max(...dashboardTrendData.value.map(d => d.amount), 1)
  return Math.round(maxAmt * n / 3)
}

// ── 年度看板方法 ──
function getGanttBarStyle(product) {
  const { start: vs, end: ve } = ganttViewRange.value
  const totalMs = ve.getTime() - vs.getTime() + 86400000
  const ps = new Date(product.start_date)
  const pe = product.end_date ? new Date(product.end_date) : ps
  const cs = Math.max(ps.getTime(), vs.getTime())
  const ce = Math.min(pe.getTime() + 86400000, ve.getTime() + 86400000)
  const left = Math.max(0, (cs - vs.getTime()) / totalMs * 100)
  const width = Math.max(0.8, (ce - cs) / totalMs * 100)
  const colors = { '募集中': '#007AFF', '即将开始': '#FF9500', '已结束': '#8E8E93' }
  return { left: left + '%', width: width + '%', background: colors[product.status] || '#5856D6' }
}


async function toggleDashboardGroup(groupId) {
  const idx = expandedDashboardGroups.value.indexOf(groupId)
  if (idx > -1) {
    expandedDashboardGroups.value.splice(idx, 1)
  } else {
    expandedDashboardGroups.value.push(groupId)
    if (!dashboardMembersData.value[groupId]) {
      try {
        const res = await analysisApi.groupMembers(groupId, 'year')
        const sorted = (res.members || []).sort((a, b) => b.sales - a.sales)
        dashboardMembersData.value = { ...dashboardMembersData.value, [groupId]: sorted }
      } catch {
        dashboardMembersData.value = { ...dashboardMembersData.value, [groupId]: [] }
      }
    }
  }
}

function getMemberPct(groupId, member) {
  const list = dashboardMembersData.value[groupId] || []
  const total = list.reduce((s, m) => s + m.sales, 0)
  return total ? Math.round(member.sales / total * 100) : 0
}

function getTopMemberPct(groupId) {
  const list = dashboardMembersData.value[groupId] || []
  if (!list.length) return 0
  const total = list.reduce((s, m) => s + m.sales, 0)
  const top = Math.max(...list.map(m => m.sales))
  return total ? Math.round(top / total * 100) : 0
}

function getBalanceClass(groupId) {
  const p = getTopMemberPct(groupId)
  if (p < 25) return 'balance-excellent'
  if (p < 40) return 'balance-good'
  return 'balance-warning'
}

function getBalanceText(groupId) {
  const p = getTopMemberPct(groupId)
  if (p < 25) return '优秀'
  if (p < 40) return '良好'
  return '注意'
}

async function setDashboardYear(year) {
  dashboardYear.value = year
  dashboardMembersData.value = {}
  expandedDashboardGroups.value = []
  try {
    const [compareRes, trendRes] = await Promise.all([
      analysisApi.groupComparison('year'),
      analysisApi.salesTrend({ year, group_by: 'month' })
    ])
    dashboardCompareGroups.value = compareRes
    dashboardTrendData.value = trendRes
  } catch (e) {
    console.error('加载看板数据失败:', e)
  }
}

// ── 计算属性（通用）──
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
  if (!num && num !== 0) return '0'
  const rounded = Math.round(Number(num) * 10) / 10
  return rounded.toLocaleString('zh-CN', { maximumFractionDigits: 1 })
}

function getRateClass(rate) {
  if (rate >= 100) return 'rate-green'
  if (rate >= 80) return 'rate-yellow'
  if (rate >= 50) return 'rate-orange'
  return 'rate-red'
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

/* ── 年度经营看板 ── */
.dashboard-controls {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  margin-bottom: 20px;
}
.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.control-label {
  font-size: 13px;
  color: #6E6E73;
  font-weight: 500;
  white-space: nowrap;
}

/* 甘特图 */
.gantt-header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.gantt-count-badge {
  font-size: 13px;
  font-weight: 600;
  color: #007AFF;
  background: #E8F4FD;
  padding: 4px 12px;
  border-radius: 20px;
}
.gantt-legend {
  display: flex;
  gap: 14px;
}
.gantt-legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #6E6E73;
}
.gantt-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.gantt-wrapper {
  width: 100%;
  overflow-x: auto;
}
.gantt-header-row {
  display: flex;
  border-bottom: 2px solid #E5E5EA;
  background: #F5F5F7;
  position: sticky;
  top: 0;
  z-index: 2;
}
.gantt-name-col {
  width: 160px;
  min-width: 160px;
  padding: 10px 14px;
  font-size: 13px;
  color: #1D1D1F;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-right: 1px solid #E5E5EA;
}
.gantt-header-cell {
  font-weight: 600;
  color: #6E6E73;
  font-size: 12px;
}
.gantt-timeline-area {
  flex: 1;
  position: relative;
  min-width: 0;
}
.gantt-header-cells {
  display: flex;
}
.gantt-col-header {
  padding: 10px 0;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #6E6E73;
  border-right: 1px solid #E5E5EA;
}
.gantt-rows-wrapper {
  max-height: 520px;
  overflow-y: auto;
}
.gantt-row-item {
  display: flex;
  border-bottom: 1px solid #F0F0F0;
  background: #fff;
}
.gantt-row-alt {
  background: #FAFAFA;
}
.gantt-timeline-row {
  position: relative;
  display: flex;
}
.gantt-grid-col {
  border-right: 1px solid #F0F0F0;
  height: 32px;
  flex-shrink: 0;
}
.gantt-bar {
  position: absolute;
  top: 5px;
  height: 22px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  overflow: hidden;
  cursor: pointer;
  transition: filter 0.15s;
  min-width: 4px;
}
.gantt-bar:hover {
  filter: brightness(0.9);
}
.gantt-bar-text {
  font-size: 11px;
  color: white;
  font-weight: 600;
  padding: 0 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gantt-empty {
  text-align: center;
  padding: 48px;
  color: #8E8E93;
  font-size: 14px;
}

/* 营业部战队排行 */
.ranking-subtitle {
  font-size: 13px;
  color: #8E8E93;
}
.team-ranking-list {
  display: flex;
  flex-direction: column;
}
.team-item {
  border-bottom: 1px solid #F0F0F0;
}
.team-item:last-child {
  border-bottom: none;
}
.team-main-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  gap: 16px;
  transition: background 0.15s;
}
.team-main-row:hover {
  background: #F9F9FB;
}
.team-rank-col {
  width: 40px;
  flex-shrink: 0;
}
.rank-medal {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  background: #E5E5EA;
  color: #6E6E73;
}
.medal-1 { background: linear-gradient(135deg, #FFD700, #FFA500); color: white; }
.medal-2 { background: linear-gradient(135deg, #C0C0C0, #A0A0A0); color: white; }
.medal-3 { background: linear-gradient(135deg, #CD7F32, #B87333); color: white; }
.team-name-col {
  width: 110px;
  font-size: 15px;
  font-weight: 600;
  color: #1D1D1F;
  flex-shrink: 0;
}
.team-bar-col {
  flex: 1;
  min-width: 0;
}
.team-sales-track {
  height: 8px;
  background: #E5E5EA;
  border-radius: 4px;
  overflow: hidden;
}
.team-sales-fill {
  height: 100%;
  background: linear-gradient(90deg, #007AFF, #5856D6);
  border-radius: 4px;
  transition: width 0.4s ease;
}
.team-sales-col {
  width: 120px;
  text-align: right;
  font-size: 15px;
  font-weight: 700;
  color: #007AFF;
  flex-shrink: 0;
}
.team-percap-col {
  width: 140px;
  text-align: right;
  font-size: 13px;
  color: #6E6E73;
  flex-shrink: 0;
}
.team-percap-col strong {
  color: #1D1D1F;
}
.unit {
  font-size: 11px;
  color: #8E8E93;
  margin-left: 2px;
}
.team-stars-col {
  width: 90px;
  text-align: center;
  flex-shrink: 0;
}
.star-icon {
  font-size: 15px;
  color: #E5E5EA;
}
.star-icon.lit {
  color: #FFCC00;
}
.team-expand-col {
  width: 28px;
  flex-shrink: 0;
  text-align: center;
}
.expand-chevron {
  font-size: 20px;
  color: #8E8E93;
  display: inline-block;
  transform: rotate(0deg);
  transition: transform 0.2s;
  line-height: 1;
}
.expand-chevron.open {
  transform: rotate(90deg);
}

/* 成员展开面板 */
.team-members-panel {
  padding: 12px 20px 20px 72px;
  background: #F9F9FB;
  border-top: 1px solid #F0F0F0;
}
.panel-loading {
  padding: 16px;
  color: #8E8E93;
  font-size: 13px;
}
.member-contrib-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
}
.member-contrib-name {
  width: 80px;
  font-size: 13px;
  color: #1D1D1F;
  font-weight: 500;
  flex-shrink: 0;
}
.member-contrib-track {
  flex: 1;
  height: 8px;
  background: #E5E5EA;
  border-radius: 4px;
  overflow: hidden;
}
.member-contrib-fill {
  height: 100%;
  background: linear-gradient(90deg, #34C759, #30D158);
  border-radius: 4px;
  transition: width 0.4s ease;
}
.member-contrib-amount {
  width: 90px;
  text-align: right;
  font-size: 13px;
  color: #007AFF;
  font-weight: 600;
  flex-shrink: 0;
}
.member-contrib-pct {
  width: 45px;
  text-align: right;
  font-size: 13px;
  color: #6E6E73;
  flex-shrink: 0;
}
.team-balance-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #E5E5EA;
}
.balance-label {
  font-size: 12px;
  color: #6E6E73;
}
.balance-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}
.balance-excellent { background: #D1FAE5; color: #059669; }
.balance-good      { background: #FEF3C7; color: #D97706; }
.balance-warning   { background: #FEE2E2; color: #DC2626; }
.balance-hint {
  font-size: 12px;
  color: #8E8E93;
}

/* 全年销售走势图 */
.annual-total-hero {
  text-align: center;
  padding: 12px 0 20px;
  border-bottom: 1px solid #F0F0F0;
  margin-bottom: 16px;
}
.annual-total-label {
  font-size: 13px;
  color: #8E8E93;
  font-weight: 500;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.annual-total-value {
  font-size: 44px;
  font-weight: 800;
  color: #1D1D1F;
  line-height: 1;
  letter-spacing: -1px;
}
.annual-total-unit {
  font-size: 18px;
  font-weight: 500;
  color: #6E6E73;
  letter-spacing: 0;
}
.annual-svg-chart-container {
  width: 100%;
  overflow-x: auto;
}
.annual-svg-chart {
  width: 100%;
  min-width: 600px;
  display: block;
  height: 200px;
}
.annual-chart-legend {
  display: flex;
  gap: 20px;
  justify-content: center;
  font-size: 12px;
  color: #6E6E73;
}
.legend-bar-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.legend-bar-dot {
  width: 12px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}
.legend-line-dot {
  width: 20px;
  height: 2px;
  border-radius: 1px;
  display: inline-block;
}
</style>
