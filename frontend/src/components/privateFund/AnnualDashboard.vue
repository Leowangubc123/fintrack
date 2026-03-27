<template>
  <div class="annual-dashboard">
    <!-- 四个KPI卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card assessed">
        <div class="kpi-label">本年度总考核销量</div>
        <div class="kpi-value assessed">{{ formatNumber(stats.total_assessed_sales) }}万</div>
        <div class="kpi-sub">实际销量 × 销售系数</div>
      </div>
      <div class="kpi-card actual">
        <div class="kpi-label">本年度总实际销量</div>
        <div class="kpi-value">{{ formatNumber(stats.total_actual_sales) }}万</div>
        <div class="kpi-sub">原始销售金额</div>
      </div>
      <div class="kpi-card redeem">
        <div class="kpi-label">本年度总赎回</div>
        <div class="kpi-value redeem">{{ formatNumber(stats.total_redemption) }}万</div>
        <div class="kpi-sub">客户赎回金额</div>
      </div>
      <div class="kpi-card net">
        <div class="kpi-label">本年度净销量</div>
        <div class="kpi-value net">{{ formatNumber(stats.net_sales) }}万</div>
        <div class="kpi-sub">实际销量 - 总赎回</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 营业部月度考核销量 -->
      <div class="chart-card full-width">
        <div class="chart-header">
          <div>
            <div class="chart-title">营业部月度考核销量</div>
            <div class="chart-subtitle">2026年度各营业部每月考核销量走势</div>
          </div>
        </div>
        <div ref="monthlyChart" class="chart-content" style="height: 300px;"></div>
      </div>

      <!-- 个人TOP10 + 产品销量分布 -->
      <div class="chart-card">
        <div class="chart-header">
          <div>
            <div class="chart-title">个人考核销量 TOP10</div>
            <div class="chart-subtitle">销售人员业绩排名（按考核销量）</div>
          </div>
        </div>
        <div ref="memberChart" class="chart-content" style="height: 280px;"></div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <div>
            <div class="chart-title">产品销量分布</div>
            <div class="chart-subtitle">各产品实际销量对比</div>
          </div>
        </div>
        <div ref="productChart" class="chart-content" style="height: 280px;"></div>
      </div>
    </div>

    <!-- 年度销售明细表格 -->
    <div class="data-table-container">
      <div class="table-header">
        <div class="table-title">年度销售明细</div>
        <div class="table-tabs">
          <span
            class="table-tab"
            :class="{ active: viewMode === 'all' }"
            @click="viewMode = 'all'"
          >全部</span>
          <span
            class="table-tab"
            :class="{ active: viewMode === 'group' }"
            @click="viewMode = 'group'"
          >按营业部</span>
          <span
            class="table-tab"
            :class="{ active: viewMode === 'member' }"
            @click="viewMode = 'member'"
          >按个人</span>
        </div>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>产品</th>
              <th>策略类型</th>
              <th>销售人员</th>
              <th>营业部</th>
              <th>实际销量(万)</th>
              <th>考核销量(万)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in tableData" :key="record.id">
              <td>{{ record.transaction_date }}</td>
              <td>{{ record.product_name }}</td>
              <td>{{ record.strategy_type }}</td>
              <td>{{ record.member_name }}</td>
              <td>{{ record.group_name }}</td>
              <td>{{ record.amount }}万</td>
              <td class="assessed-highlight">{{ record.assessed_amount }}万</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { privateFundApi } from '../../api'

const stats = ref({
  total_assessed_sales: 0,
  total_actual_sales: 0,
  total_redemption: 0,
  net_sales: 0
})

const viewMode = ref('all')
const salesRecords = ref([])
const monthlyChart = ref(null)
const memberChart = ref(null)
const productChart = ref(null)

let monthlyChartInstance = null
let memberChartInstance = null
let productChartInstance = null

const tableData = computed(() => {
  if (viewMode.value === 'all') {
    return salesRecords.value
  }
  // 按营业部或个人分组汇总逻辑
  return salesRecords.value
})

const formatNumber = (num) => {
  if (!num) return '0'
  return parseFloat(num).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 1 })
}

const initMonthlyChart = (data) => {
  if (!monthlyChart.value) return

  monthlyChartInstance = echarts.init(monthlyChart.value)

  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

  // 按营业部和月份分组数据
  const groupNames = [...new Set(data.map(d => d.group_name))]
  const series = groupNames.map((group, index) => {
    const groupData = data.filter(d => d.group_name === group)
    const monthlyData = months.map((_, monthIndex) => {
      const monthRecords = groupData.filter(d => {
        const date = new Date(d.transaction_date)
        return date.getMonth() === monthIndex
      })
      return monthRecords.reduce((sum, r) => sum + (r.assessed_amount || 0), 0)
    })

    const colors = ['#7C3AED', '#007AFF', '#34C759', '#FF9500', '#FF3B30', '#5856D6']
    return {
      name: group,
      type: 'bar',
      data: monthlyData,
      itemStyle: { color: colors[index % colors.length] }
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: groupNames,
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months
    },
    yAxis: {
      type: 'value',
      name: '考核销量(万)'
    },
    series
  }

  monthlyChartInstance.setOption(option)
}

const initMemberChart = (data) => {
  if (!memberChart.value) return

  memberChartInstance = echarts.init(memberChart.value)

  // 按销售人员汇总考核销量
  const memberStats = {}
  data.forEach(d => {
    if (!memberStats[d.member_name]) {
      memberStats[d.member_name] = 0
    }
    memberStats[d.member_name] += d.assessed_amount || 0
  })

  const sortedMembers = Object.entries(memberStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '考核销量(万)'
    },
    yAxis: {
      type: 'category',
      data: sortedMembers.map(m => m[0]).reverse(),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: sortedMembers.map(m => m[1]).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#7C3AED' },
          { offset: 1, color: '#A855F7' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}万'
      }
    }]
  }

  memberChartInstance.setOption(option)
}

const initProductChart = (data) => {
  if (!productChart.value) return

  productChartInstance = echarts.init(productChart.value)

  // 按产品汇总实际销量
  const productStats = {}
  data.forEach(d => {
    if (!productStats[d.product_name]) {
      productStats[d.product_name] = 0
    }
    productStats[d.product_name] += d.amount || 0
  })

  const pieData = Object.entries(productStats).map(([name, value]) => ({
    name,
    value: parseFloat(value.toFixed(2))
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}万 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data: pieData
    }]
  }

  productChartInstance.setOption(option)
}

const loadStats = async () => {
  try {
    const res = await privateFundApi.getAnnualStats()
    stats.value = res
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

const loadSalesRecords = async () => {
  try {
    const res = await privateFundApi.getAnnualSales()
    salesRecords.value = res

    // 初始化图表
    initMonthlyChart(res)
    initMemberChart(res)
    initProductChart(res)
  } catch (error) {
    ElMessage.error('加载销售记录失败')
  }
}

const handleResize = () => {
  monthlyChartInstance?.resize()
  memberChartInstance?.resize()
  productChartInstance?.resize()
}

onMounted(() => {
  loadStats()
  loadSalesRecords()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.annual-dashboard {
  padding: 24px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.kpi-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.kpi-card.assessed::before { background: linear-gradient(90deg, #007AFF, #5856D6); }
.kpi-card.actual::before { background: linear-gradient(90deg, #7C3AED, #A855F7); }
.kpi-card.redeem::before { background: linear-gradient(90deg, #FF3B30, #FF6B35); }
.kpi-card.net::before { background: linear-gradient(90deg, #34C759, #30D158); }

.kpi-label {
  font-size: 13px;
  color: #6E6E73;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #1D1D1F;
}

.kpi-value.assessed {
  background: linear-gradient(135deg, #007AFF, #5856D6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.kpi-value.redeem {
  color: #FF3B30;
}

.kpi-value.net {
  color: #34C759;
}

.kpi-sub {
  font-size: 12px;
  color: #8E8E93;
  margin-top: 4px;
}

.charts-grid {
  display: grid;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-header {
  padding: 20px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.chart-subtitle {
  font-size: 13px;
  color: #8E8E93;
}

.chart-content {
  padding: 20px;
}

.data-table-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.table-tabs {
  display: flex;
  gap: 8px;
}

.table-tab {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  background: #F5F5F7;
  color: #6E6E73;
  transition: all 0.2s;
}

.table-tab:hover {
  background: #E5E5EA;
}

.table-tab.active {
  background: #7C3AED;
  color: white;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #FAFAFB;
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #6E6E73;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.data-table td {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 14px;
  color: #1D1D1F;
}

.data-table tr:hover {
  background: #FAFAFB;
}

.assessed-highlight {
  color: #007AFF;
  font-weight: 700;
}

@media (min-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr 1fr;
  }
  .chart-card.full-width {
    grid-column: 1 / -1;
  }
}
</style>
