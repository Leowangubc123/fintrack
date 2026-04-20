<template>
  <div class="advisory-member-view">
    <!-- Filters -->
    <div class="filter-bar">
      <el-select v-if="isNew" v-model="selectedYear" style="width: 120px">
        <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
      </el-select>

      <el-select v-model="filterGroup" placeholder="全部营业部" clearable style="width: 160px">
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
      </el-select>

      <el-select v-model="filterMember" placeholder="全部员工" clearable style="width: 140px">
        <el-option v-for="m in filteredMembers" :key="m.id" :label="m.name" :value="m.id" />
      </el-select>

      <el-select v-model="filterProduct" placeholder="全部产品" clearable style="width: 120px">
        <el-option v-for="p in productOptions" :key="p" :label="p" :value="p" />
      </el-select>

      <el-button type="primary" @click="exportToExcel">
        <el-icon><Download /></el-icon>导出Excel
      </el-button>
    </div>

    <!-- Data Table -->
    <div class="table-container">
      <el-table
        :data="paginatedData"
        stripe
        @sort-change="handleSortChange"
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" />

        <el-table-column prop="member_name" label="员工" width="70" sortable />

        <el-table-column prop="group_name" label="营业部" width="100" sortable />

        <el-table-column label="千1" align="center" min-width="80">
          <el-table-column prop="products.千1.households" label="户" width="70" align="right" sortable />
        </el-table-column>

        <el-table-column label="千3" align="center" min-width="80">
          <el-table-column prop="products.千3.households" label="户" width="70" align="right" sortable />
        </el-table-column>

        <el-table-column label="万2及其他" align="center" min-width="100">
          <el-table-column prop="products.万2及其他.households" label="户" width="70" align="right" sortable />
        </el-table-column>

        <el-table-column label="ETF投顾" align="center" min-width="90">
          <el-table-column prop="products.ETF投顾.households" label="户" width="75" align="right" sortable />
        </el-table-column>

        <el-table-column label="量化T策略" align="center" min-width="100">
          <el-table-column prop="products.量化T策略.households" label="户" width="70" align="right" sortable />
        </el-table-column>

        <el-table-column label="GWT" align="center" min-width="80">
          <el-table-column prop="products.GWT.households" label="户" width="70" align="right" sortable />
        </el-table-column>

        <el-table-column prop="total_households" label="合计户数" min-width="90" align="right" sortable>
          <template #default="{ row }">
            <strong>{{ row.total_households }}</strong>
          </template>
        </el-table-column>

        <el-table-column prop="total_assets" label="签约资产" min-width="120" align="right" sortable>
          <template #default="{ row }">
            {{ row.total_assets.toFixed(2) }}万
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Pagination -->
    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="filteredData.length"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { advisoryApi } from '../../api/advisory.js'
import { groupsApi, membersApi } from '../../api/index.js'

const props = defineProps({
  scope: {
    type: String,
    default: 'new',
    validator: (v) => ['new', 'stock'].includes(v)
  }
})

const isNew = computed(() => props.scope === 'new')

const selectedYear = ref(new Date().getFullYear())
const years = computed(() => {
  const current = new Date().getFullYear()
  return [current, current - 1]
})

const groups = ref([])
const members = ref([])
const subscriptions = ref([])
const loading = ref(false)

const filterGroup = ref(null)
const filterMember = ref(null)
const filterProduct = ref(null)

const currentPage = ref(1)
const pageSize = ref(20)
const sortProp = ref('')
const sortOrder = ref('')

const productOptions = ['万2及其他', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT']

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

const fetchSubscriptions = async () => {
  loading.value = true
  try {
    const params = {
      scope: props.scope,
      page_size: 10000
    }
    if (isNew.value) {
      params.year = selectedYear.value
    }
    const res = await advisoryApi.getSubscriptions(params)
    subscriptions.value = res.items || []
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
    ElMessage.error('获取签约数据失败')
  } finally {
    loading.value = false
  }
}

const filteredMembers = computed(() => {
  if (!filterGroup.value) return members.value
  return members.value.filter(m => m.group_id === filterGroup.value)
})

const memberStats = computed(() => {
  const stats = {}

  // Initialize for all members
  members.value.forEach(member => {
    stats[member.id] = {
      member_id: member.id,
      member_name: member.name,
      group_id: member.group_id,
      group_name: groups.value.find(g => g.id === member.group_id)?.name || '-',
      total_households: 0,
      total_assets: 0,
      total_income: 0,
      products: {}
    }
    productOptions.forEach(p => {
      stats[member.id].products[p] = { households: 0, assets: 0 }
    })
  })

  // Aggregate data
  subscriptions.value.forEach(sub => {
    const memberId = sub.member_id
    if (!stats[memberId]) return

    const converted = sub.converted_households || 1
    const assets = parseFloat(sub.asset_amount || 0)
    const income = parseFloat(sub.advisory_income || 0)

    stats[memberId].total_households += converted
    stats[memberId].total_assets += assets / 10000
    stats[memberId].total_income += income

    const product = sub.product_type
    if (stats[memberId].products[product]) {
      stats[memberId].products[product].households += converted
      stats[memberId].products[product].assets += assets / 10000
    }
  })

  return Object.values(stats)
})

const filteredData = computed(() => {
  let data = memberStats.value

  // Apply filters
  if (filterGroup.value) {
    data = data.filter(m => m.group_id === filterGroup.value)
  }
  if (filterMember.value) {
    data = data.filter(m => m.member_id === filterMember.value)
  }
  if (filterProduct.value) {
    data = data.filter(m => m.products[filterProduct.value]?.households > 0)
  }

  // Apply sorting
  if (sortProp.value && sortOrder.value) {
    data = [...data].sort((a, b) => {
      let aVal, bVal
      if (sortProp.value.includes('.')) {
        const keys = sortProp.value.split('.')
        aVal = keys.reduce((obj, key) => obj?.[key], a)
        bVal = keys.reduce((obj, key) => obj?.[key], b)
      } else {
        aVal = a[sortProp.value]
        bVal = b[sortProp.value]
      }

      if (sortOrder.value === 'ascending') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }

  return data
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

const handleSortChange = ({ prop, order }) => {
  sortProp.value = prop
  sortOrder.value = order
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const exportToExcel = () => {
  const exportData = filteredData.value.map(m => ({
    '员工': m.member_name,
    '营业部': m.group_name,
    '万2及其他(户)': m.products.万2及其他.households,
    '千1(户)': m.products.千1.households,
    '千3(户)': m.products.千3.households,
    'ETF投顾(户)': m.products.ETF投顾.households,
    '量化T策略(户)': m.products.量化T策略.households,
    'GWT(户)': m.products.GWT.households,
    '合计户数': m.total_households,
    '签约资产(万)': m.total_assets.toFixed(2)
  }))

  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '投顾签约明细')

  const filename = `投顾签约明细_${selectedYear.value}_${new Date().toISOString().split('T')[0]}.xlsx`
  XLSX.writeFile(wb, filename)

  ElMessage.success('导出成功')
}

watch([selectedYear, filterGroup], () => {
  filterMember.value = null
  fetchSubscriptions()
})

watch(() => props.scope, () => {
  fetchSubscriptions()
})

onMounted(() => {
  fetchGroups()
  fetchMembers()
  fetchSubscriptions()
  window.addEventListener('advisory-data-imported', fetchSubscriptions)
})

onBeforeUnmount(() => {
  window.removeEventListener('advisory-data-imported', fetchSubscriptions)
})
</script>

<style scoped>
.advisory-member-view {
  padding: 0;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
}

:deep(.el-table th) {
  background: #F9FAFB;
  font-weight: 600;
  color: #374151;
}

:deep(.el-table td) {
  padding: 10px 0;
  color: #111827;
}

:deep(.el-button--primary) {
  background: #1EAEDB;
  border-color: #1EAEDB;
}

.pagination-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
