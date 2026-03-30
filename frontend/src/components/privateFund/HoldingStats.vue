<template>
  <div class="holding-stats">
    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card primary">
        <div class="kpi-label">考核保有量</div>
        <div class="kpi-value primary">{{ formatNumber(stats.total_assessed_holding) }}万</div>
        <div class="kpi-sub">保有市值 × 保有系数</div>
      </div>
      <div class="kpi-card secondary">
        <div class="kpi-label">实际保有市值</div>
        <div class="kpi-value secondary">{{ formatNumber(stats.total_market_value) }}万</div>
        <div class="kpi-sub">原始保有市值合计</div>
      </div>
      <div class="kpi-card info">
        <div class="kpi-label">最近更新日期</div>
        <div class="kpi-value info">{{ formatDate(stats.latest_record_date) }}</div>
        <div class="kpi-sub">数据时点更新时间</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 左侧：考核保有量趋势 -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title-wrap">
            <div class="chart-title">考核保有量趋势</div>
            <div class="update-date">更新于 {{ formatDate(stats.latest_record_date) }}</div>
          </div>
        </div>
        <div class="chart-subtitle">根据数据上传时点更新</div>
        <div ref="trendChart" class="chart-content"></div>
      </div>

      <!-- 右侧：营业部考核保有量分布 -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title-wrap">
            <div class="chart-title">营业部考核保有量分布</div>
            <div class="update-date">更新于 {{ formatDate(stats.latest_record_date) }}</div>
          </div>
        </div>
        <div class="chart-subtitle">各营业部考核保有量排名</div>
        <div ref="groupChart" class="chart-content"></div>
      </div>
    </div>

    <!-- 保有明细表格 -->
    <div class="data-table-container">
      <div class="table-header">
        <div class="table-title-wrap">
          <div class="table-title">保有明细</div>
          <div class="update-date">更新于 {{ formatDate(stats.latest_record_date) }}</div>
        </div>
        <div class="table-actions">
          <el-select
            v-model="selectedGroup"
            placeholder="全部营业部"
            clearable
            style="width: 160px"
            @change="onGroupFilterChange"
          >
            <el-option
              v-for="group in availableGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon> 上传保有数据
          </el-button>
        </div>
      </div>

      <div class="table-wrapper">
        <el-table :data="filteredHoldings" style="width: 100%" v-loading="loading">
          <el-table-column prop="product_name" label="产品名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="product_code" label="产品代码" width="120" />
          <el-table-column prop="group_name" label="营业部" width="120" />
          <el-table-column prop="holding_market_value" label="保有市值(万)" width="130" align="right">
            <template #default="{ row }">
              <span class="market-value">{{ formatNumber(row.holding_market_value) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="holding_coefficient" label="保有系数" width="100" align="center">
            <template #default="{ row }">
              <span class="coefficient-badge">{{ row.holding_coefficient }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="assessed_holding" label="考核保有量(万)" width="140" align="right">
            <template #default="{ row }">
              <span class="assessed-highlight">{{ formatNumber(row.assessed_holding) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传保有数据"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="uploadForm" label-position="top">
        <el-form-item label="数据日期" required>
          <el-date-picker
            v-model="uploadForm.recordDate"
            type="date"
            placeholder="选择数据日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="数据文件 (Excel)" required>
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".xlsx,.xls"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="upload-tip">
                请上传Excel文件，包含以下列：产品名称、产品代码、所属营业部、保有市值<br>
                系统将根据产品代码自动匹配保有系数并计算考核保有量
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import { privateFundApi, groupsApi } from '../../api'

const loading = ref(false)
const uploading = ref(false)
const showUploadDialog = ref(false)
const uploadForm = ref({
  recordDate: new Date().toISOString().split('T')[0]
})
const uploadFile = ref(null)
const uploadRef = ref(null)

const stats = ref({
  total_assessed_holding: 0,
  total_market_value: 0,
  record_count: 0,
  latest_record_date: null,
  group_stats: [],
  trend_data: []
})

const holdings = ref([])
const availableGroups = ref([])
const selectedGroup = ref('')

const trendChart = ref(null)
const groupChart = ref(null)
let trendChartInstance = null
let groupChartInstance = null

const filteredHoldings = computed(() => {
  if (!selectedGroup.value) return holdings.value
  return holdings.value.filter(h => h.group_id === selectedGroup.value || h.group_name === selectedGroup.value)
})

const formatNumber = (num) => {
  if (!num) return '0'
  return parseFloat(num).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

const initTrendChart = () => {
  if (!trendChart.value) return

  trendChartInstance = echarts.init(trendChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const data = params[0]
        return `${data.name}<br/>考核保有量: ${data.value}万`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: stats.value.trend_data.map(d => {
        const date = new Date(d.record_date)
        return `${date.getMonth() + 1}/${date.getDate()}`
      }),
      axisLine: { lineStyle: { color: '#E5E5EA' } },
      axisLabel: { color: '#8E8E93', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '考核保有量(万)',
      nameTextStyle: { color: '#8E8E93', fontSize: 11 },
      splitLine: { lineStyle: { type: 'dashed', color: '#E5E5EA' } },
      axisLabel: { color: '#8E8E93', fontSize: 11 }
    },
    series: [{
      type: 'line',
      data: stats.value.trend_data.map(d => d.assessed_holding.toFixed(2)),
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        color: '#007AFF',
        width: 2
      },
      itemStyle: {
        color: '#007AFF',
        borderWidth: 2,
        borderColor: '#fff'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 122, 255, 0.2)' },
          { offset: 1, color: 'rgba(0, 122, 255, 0)' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: '#34C759',
          borderColor: '#fff',
          borderWidth: 3,
          shadowBlur: 10,
          shadowColor: 'rgba(52, 199, 89, 0.4)'
        }
      }
    }]
  }

  trendChartInstance.setOption(option)
}

const initGroupChart = () => {
  if (!groupChart.value) return

  groupChartInstance = echarts.init(groupChart.value)

  const sortedGroups = [...stats.value.group_stats].sort((a, b) => a.assessed_holding - b.assessed_holding)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}万'
    },
    grid: {
      left: '3%',
      right: '15%',
      top: '5%',
      bottom: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '考核保有量(万)',
      nameLocation: 'end',
      nameGap: 8,
      axisLine: { show: true, lineStyle: { color: '#E5E5EA' } },
      axisTick: { show: true },
      axisLabel: { show: true, color: '#8E8E93', fontSize: 11 },
      splitLine: { lineStyle: { type: 'dashed', color: '#E5E5EA' } }
    },
    yAxis: {
      type: 'category',
      data: sortedGroups.map(g => g.group_name),
      axisLabel: {
        fontSize: 12,
        color: '#1D1D1F',
        width: 80,
        overflow: 'truncate'
      },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: sortedGroups.map(g => g.assessed_holding.toFixed(2)),
      barWidth: '50%',
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#007AFF' },
          { offset: 1, color: '#5856D6' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}万',
        fontSize: 11,
        color: '#1D1D1F'
      }
    }]
  }

  groupChartInstance.setOption(option)
}

const loadStats = async () => {
  try {
    const res = await privateFundApi.getHoldingStats()
    stats.value = res
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

const loadHoldings = async () => {
  loading.value = true
  try {
    const res = await privateFundApi.getHoldings()
    holdings.value = res
  } catch (error) {
    ElMessage.error('加载保有数据失败')
  } finally {
    loading.value = false
  }
}

const loadGroups = async () => {
  try {
    const res = await groupsApi.list()
    availableGroups.value = res
  } catch (error) {
    console.error('加载营业部列表失败', error)
  }
}

const onGroupFilterChange = () => {
  // 可以在这里添加额外的筛选逻辑
}

const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

const submitUpload = async () => {
  if (!uploadForm.value.recordDate) {
    ElMessage.warning('请选择数据日期')
    return
  }
  if (!uploadFile.value) {
    ElMessage.warning('请选择Excel文件')
    return
  }

  uploading.value = true
  try {
    // 读取Excel文件
    const data = await uploadFile.value.arrayBuffer()
    const workbook = XLSX.read(data, { type: 'array' })
    const sheetName = workbook.SheetNames[0]
    const worksheet = workbook.Sheets[sheetName]
    const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

    // 解析数据（假设第一行是表头）
    const headers = jsonData[0]
    const rows = jsonData.slice(1)

    const uploadData = rows.map(row => {
      const item = {}
      headers.forEach((header, index) => {
        const value = row[index]
        if (header.includes('产品名称')) item.product_name = String(value || '')
        if (header.includes('产品代码')) item.product_code = String(value || '')
        if (header.includes('营业部')) item.group_name = String(value || '')
        if (header.includes('保有市值')) item.holding_market_value = parseFloat(value) || 0
      })
      return item
    }).filter(item => item.product_name && item.group_name)

    if (uploadData.length === 0) {
      ElMessage.warning('未能解析到有效数据，请检查文件格式')
      return
    }

    const res = await privateFundApi.uploadHoldings(uploadData, uploadForm.value.recordDate)
    ElMessage.success(`上传成功，共导入 ${res.success_count} 条记录`)

    showUploadDialog.value = false
    uploadRef.value?.clearFiles()
    uploadFile.value = null

    // 刷新数据
    await loadStats()
    await loadHoldings()
    await nextTick()
    initTrendChart()
    initGroupChart()
  } catch (error) {
    ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const handleResize = () => {
  trendChartInstance?.resize()
  groupChartInstance?.resize()
}

onMounted(() => {
  loadStats()
  loadHoldings()
  loadGroups()
  window.addEventListener('resize', handleResize)

  // 延迟初始化图表，确保DOM已渲染
  setTimeout(() => {
    initTrendChart()
    initGroupChart()
  }, 100)
})
</script>

<style scoped>
.holding-stats {
  padding: 24px;
}

/* KPI 卡片 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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

.kpi-card.primary::before { background: linear-gradient(90deg, #007AFF, #5856D6); }
.kpi-card.secondary::before { background: linear-gradient(90deg, #34C759, #30D158); }
.kpi-card.info::before { background: linear-gradient(90deg, #FF9500, #FF6B35); }

.kpi-label {
  font-size: 13px;
  color: #6E6E73;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: #1D1D1F;
}

.kpi-value.primary {
  background: linear-gradient(135deg, #007AFF, #5856D6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.kpi-value.secondary {
  color: #34C759;
}

.kpi-value.info {
  color: #FF9500;
}

.kpi-sub {
  font-size: 12px;
  color: #8E8E93;
  margin-top: 4px;
}

/* 图表区域 */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.chart-header {
  padding: 20px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.update-date {
  font-size: 12px;
  color: #8E8E93;
  background: #F5F5F7;
  padding: 4px 10px;
  border-radius: 12px;
}

.chart-subtitle {
  font-size: 13px;
  color: #8E8E93;
  padding: 4px 20px 0;
}

.chart-content {
  padding: 20px;
  height: 320px;
}

/* 数据表格 */
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

.table-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-wrapper {
  padding: 0 20px 20px;
}

.coefficient-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: rgba(124, 58, 237, 0.1);
  color: #7C3AED;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.assessed-highlight {
  color: #007AFF;
  font-weight: 700;
}

.market-value {
  color: #6E6E73;
}

.upload-tip {
  font-size: 12px;
  color: #8E8E93;
  line-height: 1.6;
  margin-top: 8px;
}

@media (max-width: 1024px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
