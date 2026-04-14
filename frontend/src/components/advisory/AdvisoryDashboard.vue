<template>
  <div class="advisory-dashboard">
    <!-- 维度切换 -->
    <div class="dimension-bar">
      <div class="dimension-tabs">
        <span
          v-for="d in dimensions"
          :key="d.key"
          class="dimension-tab"
          :class="{ active: dimension === d.key }"
          @click="dimension = d.key"
        >
          {{ d.label }}
        </span>
      </div>
      <div class="dimension-filter" v-if="dimension === 'group'">
        <el-select v-model="selectedGroup" placeholder="选择营业部" clearable style="width: 180px">
          <el-option
            v-for="g in groups"
            :key="g.id"
            :label="g.name"
            :value="g.id"
          />
        </el-select>
      </div>
      <div class="dimension-filter" v-if="dimension === 'member'">
        <el-select v-model="selectedMember" placeholder="选择员工" clearable style="width: 180px">
          <el-option
            v-for="m in members"
            :key="m.id"
            :label="m.name"
            :value="m.id"
          />
        </el-select>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">累计签约户数</div>
        <div class="kpi-value">{{ formatNumber(stats.total_households) }}<span class="unit">户</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.households_change >= 0, 'is-negative': stats.households_change < 0 }">
          较上次更新 {{ stats.households_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.households_change || 0) }}户
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">累计签约资产</div>
        <div class="kpi-value">{{ formatNumber(stats.total_assets) }}<span class="unit">万</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.assets_change >= 0, 'is-negative': stats.assets_change < 0 }">
          较上次更新 {{ stats.assets_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.assets_change || 0) }}万
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">本年投顾收入</div>
        <div class="kpi-value">{{ formatNumber(stats.total_income) }}<span class="unit">元</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.income_change >= 0, 'is-negative': stats.income_change < 0 }">
          较上次更新 {{ stats.income_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.income_change || 0) }}元
        </div>
      </div>
      <div class="kpi-card kpi-date">
        <div class="kpi-label">最近更新日期</div>
        <div class="kpi-value date">{{ stats.last_update_date || '-' }}</div>
        <div class="kpi-sub">数据时点更新</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">各产品签约分布</div>
          <div class="chart-legend">
            <span class="legend-item"><span class="dot households"></span>签约户数</span>
            <span class="legend-item"><span class="dot assets"></span>签约资产(万)</span>
          </div>
        </div>
        <div ref="productChart" class="chart-content" style="height: 320px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">年度趋势分析</div>
          <div class="chart-legend">
            <span class="legend-item"><span class="dot income"></span>投顾收入(元)</span>
            <span class="legend-item"><span class="dot line"></span>签约户数</span>
          </div>
        </div>
        <div ref="trendChart" class="chart-content" style="height: 320px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { advisoryApi } from '../../api/advisory.js'
import { groupsApi, membersApi } from '../../api/index.js'

const dimensions = [
  { key: 'all', label: '全辖区' },
  { key: 'group', label: '营业部' },
  { key: 'member', label: '个人' }
]

const dimension = ref('all')
const selectedGroup = ref(null)
const selectedMember = ref(null)
const groups = ref([])
const members = ref([])

const stats = ref({
  total_households: 0,
  total_assets: 0,
  total_income: 0,
  households_change: 0,
  assets_change: 0,
  income_change: 0,
  last_update_date: null,
  product_distribution: [],
  trend_data: []
})

const productChart = ref(null)
const trendChart = ref(null)
let productChartInstance = null
let trendChartInstance = null

const productOrder = ['万2', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT']

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchMembers = async () => {
  try {
    const res = await membersApi.getAll()
    members.value = res
  } catch (error) {
    console.error('Failed to fetch members:', error)
  }
}

const fetchStats = async () => {
  try {
    const params = {
      year: new Date().getFullYear()
    }
    if (dimension.value === 'group' && selectedGroup.value) {
      params.group_id = selectedGroup.value
    }
    if (dimension.value === 'member' && selectedMember.value) {
      params.member_id = selectedMember.value
    }
    const res = await advisoryApi.getStats(params)
    stats.value = {
      ...stats.value,
      ...res
    }
    updateCharts()
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    ElMessage.error('获取统计数据失败')
  }
}

const initCharts = () => {
  if (productChart.value) {
    productChartInstance = echarts.init(productChart.value)
  }
  if (trendChart.value) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  productChartInstance?.resize()
  trendChartInstance?.resize()
}

const updateCharts = () => {
  nextTick(() => {
    updateProductChart()
    updateTrendChart()
  })
}

const updateProductChart = () => {
  if (!productChartInstance) return

  const distribution = stats.value.product_distribution || []
  const dataMap = {}
  distribution.forEach(item => {
    dataMap[item.product_type] = {
      households: item.households || 0,
      assets: item.assets || 0
    }
  })

  const householdsData = productOrder.map(p => dataMap[p]?.households || 0)
  const assetsData = productOrder.map(p => dataMap[p]?.assets || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['签约户数', '签约资产(万)'],
      right: 0,
      top: 0,
      textStyle: { color: '#6B7280', fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '12%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'value',
        name: '户数',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#F3F4F6' } },
        axisLabel: { color: '#6B7280' }
      },
      {
        type: 'value',
        name: '资产(万)',
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#6B7280' }
      }
    ],
    yAxis: {
      type: 'category',
      data: productOrder,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280' },
      axisTick: { alignWithLabel: true }
    },
    series: [
      {
        name: '签约户数',
        type: 'bar',
        data: householdsData,
        itemStyle: { color: '#0891B2', borderRadius: [0, 4, 4, 0] },
        barWidth: '40%'
      },
      {
        name: '签约资产(万)',
        type: 'bar',
        xAxisIndex: 1,
        data: assetsData,
        itemStyle: { color: '#06B6D4', borderRadius: [0, 4, 4, 0] },
        barWidth: '40%'
      }
    ]
  }

  productChartInstance.setOption(option, true)
}

const updateTrendChart = () => {
  if (!trendChartInstance) return

  const trendData = stats.value.trend_data || []
  const months = trendData.map(t => t.month + '月')
  const incomeData = trendData.map(t => t.income || 0)
  const householdsData = trendData.map(t => t.households || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280' }
    },
    yAxis: [
      {
        type: 'value',
        name: '投顾收入(元)',
        position: 'left',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#F3F4F6' } },
        axisLabel: { color: '#6B7280' }
      },
      {
        type: 'value',
        name: '签约户数',
        position: 'right',
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#6B7280' }
      }
    ],
    series: [
      {
        name: '投顾收入',
        type: 'bar',
        data: incomeData,
        itemStyle: { color: '#0891B2', borderRadius: [4, 4, 0, 0] },
        barWidth: '40%'
      },
      {
        name: '签约户数',
        type: 'line',
        yAxisIndex: 1,
        data: householdsData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#F59E0B', width: 3 },
        itemStyle: { color: '#F59E0B', borderWidth: 2, borderColor: '#fff' }
      }
    ]
  }

  trendChartInstance.setOption(option)
}

watch([dimension, selectedGroup, selectedMember], () => {
  fetchStats()
})

onMounted(() => {
  fetchGroups()
  fetchMembers()
  fetchStats()
  initCharts()
})
</script>

<style scoped>
.advisory-dashboard {
  padding: 0;
}

.dimension-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.dimension-tabs {
  display: flex;
  background: #F3F4F6;
  border-radius: 8px;
  padding: 4px;
}

.dimension-tab {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.dimension-tab:hover {
  color: #374151;
}

.dimension-tab.active {
  background: white;
  color: #0891B2;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F3F4F6;
}

.kpi-label {
  font-size: 14px;
  color: #6B7280;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.kpi-value .unit {
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  margin-left: 4px;
}

.kpi-value.date {
  font-size: 20px;
  color: #0891B2;
}

.kpi-change {
  font-size: 12px;
  font-weight: 500;
}

.kpi-change.is-positive {
  color: #10B981;
}

.kpi-change.is-negative {
  color: #EF4444;
}

.kpi-sub {
  font-size: 12px;
  color: #9CA3AF;
}

.kpi-card.kpi-date {
  background: linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%);
  border-color: #A5F3FC;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F3F4F6;
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
  color: #111827;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6B7280;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.dot.households {
  background: #0891B2;
}

.dot.assets {
  background: #06B6D4;
}

.dot.income {
  background: #0891B2;
}

.dot.line {
  background: #F59E0B;
  border-radius: 50%;
}

.chart-content {
  width: 100%;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
