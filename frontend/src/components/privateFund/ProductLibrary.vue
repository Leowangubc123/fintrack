<template>
  <div class="product-library">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="search-box">
        <el-icon class="search-icon"><Search /></el-icon>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索产品名称或代码..."
          @input="handleSearch"
        >
      </div>
      <button class="btn btn-primary" @click="showAddModal = true">
        <el-icon><Plus /></el-icon> 添加产品
      </button>
    </div>

    <!-- 按策略类型分组展示 -->
    <div v-for="strategy in strategyTypes" :key="strategy" class="strategy-section">
      <div class="strategy-header">
        <span class="strategy-name">{{ strategy }}</span>
        <span class="strategy-count">{{ getProductsByStrategy(strategy).length }}只产品</span>
      </div>
      <div class="product-list">
        <div
          v-for="product in getProductsByStrategy(strategy)"
          :key="product.id"
          class="product-row"
          @click="toggleDetail(product.id)"
        >
          <div class="product-row-main">
            <div class="product-basic-info">
              <div class="product-row-name">{{ product.name }}</div>
              <span class="product-row-code">{{ product.code }}</span>
            </div>
            <div class="product-row-info">
              <span>📊 {{ product.manager }}</span>
              <span>🌐 {{ product.distribution_scope || '全国' }}</span>
              <span>🔒 {{ product.lock_period || '无' }}</span>
            </div>
            <span class="risk-badge" :class="'risk-' + product.risk_level.toLowerCase()">
              {{ product.risk_level }}
            </span>
            <div class="coefficient-box">
              <div class="coefficient-box-label">销售系数</div>
              <div class="coefficient-box-value">{{ product.sales_coefficient }}</div>
            </div>
          </div>
          <div class="product-row-actions" @click.stop>
            <button class="btn btn-secondary btn-sm" @click="editProduct(product)">编辑</button>
            <button class="btn btn-danger btn-sm" @click="deleteProduct(product.id)">删除</button>
          </div>
        </div>

        <!-- 展开详情 -->
        <div
          v-for="product in getProductsByStrategy(strategy)"
          :key="'detail-' + product.id"
          class="product-detail-panel"
          :class="{ active: expandedProducts.includes(product.id) }"
        >
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">策略类型</div>
              <div class="detail-value">{{ product.strategy_type }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">管理人</div>
              <div class="detail-value">{{ product.manager }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">代销范围</div>
              <div class="detail-value">{{ product.distribution_scope || '全国' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">风险等级</div>
              <div class="detail-value">{{ product.risk_level }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">锁定期</div>
              <div class="detail-value">{{ product.lock_period || '无' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">销售系数</div>
              <div class="detail-value">{{ product.sales_coefficient }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">保有系数</div>
              <div class="detail-value">{{ product.holding_coefficient || '-' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">认申购费</div>
              <div class="detail-value">{{ product.subscription_fee ? product.subscription_fee + '%' : '-' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">开放期</div>
              <div class="detail-value">{{ product.open_period || '-' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">销售服务费</div>
              <div class="detail-value">{{ product.service_fee ? product.service_fee + '%' : '-' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">管理费</div>
              <div class="detail-value">{{ product.management_fee ? product.management_fee + '%' : '-' }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">业绩提成</div>
              <div class="detail-value">{{ product.performance_fee || '-' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑产品弹窗 -->
    <el-dialog
      v-model="showAddModal"
      :title="editingProduct ? '编辑产品' : '添加产品'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="productForm" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品名称" required>
              <el-input v-model="productForm.name" placeholder="请输入产品名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品代码" required>
              <el-input v-model="productForm.code" placeholder="如：SM2024A001" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="管理人" required>
              <el-input v-model="productForm.manager" placeholder="请输入管理人名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="代销范围">
              <el-input v-model="productForm.distribution_scope" placeholder="如：全国/华东地区" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="策略类型" required>
              <el-select v-model="productForm.strategy_type" placeholder="请选择" style="width: 100%" @change="onStrategyChange">
                <el-option label="量化指增" value="量化指增" />
                <el-option label="量化选股" value="量化选股" />
                <el-option label="主观多头" value="主观多头" />
                <el-option label="量化中性" value="量化中性" />
                <el-option label="量化套利" value="量化套利" />
                <el-option label="全天候策略" value="全天候策略" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="风险等级" required>
              <el-select v-model="productForm.risk_level" placeholder="请选择" style="width: 100%">
                <el-option label="R3 - 中等风险" value="R3" />
                <el-option label="R4 - 中高风险" value="R4" />
                <el-option label="R5 - 高风险" value="R5" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item v-if="productForm.strategy_type === '其他'" label="自定义策略">
          <el-input v-model="productForm.custom_strategy" placeholder="请输入自定义策略类型" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="锁定期">
              <el-input v-model="productForm.lock_period" placeholder="如：1年/2年" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开放期">
              <el-input v-model="productForm.open_period" placeholder="如：每月5日为开放日" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="销售系数" required>
              <el-input-number v-model="productForm.sales_coefficient" :min="0.1" :max="5" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="保有系数">
              <el-input-number v-model="productForm.holding_coefficient" :min="0" :max="5" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="认申购费(%)">
              <el-input-number v-model="productForm.subscription_fee" :min="0" :max="10" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="销售服务费(%)">
              <el-input-number v-model="productForm.service_fee" :min="0" :max="10" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="管理费(%)">
              <el-input-number v-model="productForm.management_fee" :min="0" :max="10" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业绩提成">
              <el-input v-model="productForm.performance_fee" placeholder="如：超额收益20%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="showAddModal = false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { privateFundApi } from '../../api'

const products = ref([])
const searchKeyword = ref('')
const showAddModal = ref(false)
const editingProduct = ref(null)
const expandedProducts = ref([])

const strategyTypes = ['量化指增', '量化选股', '主观多头', '量化中性', '量化套利', '全天候策略', '其他']

const productForm = ref({
  name: '',
  code: '',
  manager: '',
  distribution_scope: '',
  strategy_type: '',
  custom_strategy: '',
  risk_level: '',
  lock_period: '',
  open_period: '',
  sales_coefficient: 1.0,
  holding_coefficient: 1.0,
  subscription_fee: null,
  service_fee: null,
  management_fee: null,
  performance_fee: ''
})

const filteredProducts = computed(() => {
  if (!searchKeyword.value) return products.value
  const keyword = searchKeyword.value.toLowerCase()
  return products.value.filter(p =>
    p.name.toLowerCase().includes(keyword) ||
    p.code.toLowerCase().includes(keyword)
  )
})

const getProductsByStrategy = (strategy) => {
  return filteredProducts.value.filter(p => p.strategy_type === strategy)
}

const toggleDetail = (productId) => {
  const index = expandedProducts.value.indexOf(productId)
  if (index > -1) {
    expandedProducts.value.splice(index, 1)
  } else {
    expandedProducts.value.push(productId)
  }
}

const onStrategyChange = (value) => {
  if (value !== '其他') {
    productForm.value.custom_strategy = ''
  }
}

const editProduct = (product) => {
  editingProduct.value = product
  productForm.value = { ...product }
  showAddModal.value = true
}

const deleteProduct = async (productId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个产品吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await privateFundApi.deleteProduct(productId)
    ElMessage.success('删除成功')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const saveProduct = async () => {
  try {
    // 合并自定义策略类型
    const formData = { ...productForm.value }
    if (formData.strategy_type === '其他' && formData.custom_strategy) {
      formData.strategy_type = formData.custom_strategy
    }
    delete formData.custom_strategy

    if (editingProduct.value) {
      await privateFundApi.updateProduct(editingProduct.value.id, formData)
      ElMessage.success('更新成功')
    } else {
      await privateFundApi.createProduct(formData)
      ElMessage.success('添加成功')
    }
    showAddModal.value = false
    resetForm()
    loadProducts()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const resetForm = () => {
  editingProduct.value = null
  productForm.value = {
    name: '',
    code: '',
    manager: '',
    distribution_scope: '',
    strategy_type: '',
    custom_strategy: '',
    risk_level: '',
    lock_period: '',
    open_period: '',
    sales_coefficient: 1.0,
    holding_coefficient: 1.0,
    subscription_fee: null,
    service_fee: null,
    management_fee: null,
    performance_fee: ''
  }
}

const loadProducts = async () => {
  try {
    const res = await privateFundApi.getProducts()
    products.value = res
  } catch (error) {
    ElMessage.error('加载产品列表失败')
  }
}

const handleSearch = () => {
  // 搜索通过计算属性自动处理
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.product-library {
  padding: 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.search-box {
  flex: 1;
  max-width: 400px;
  position: relative;
}

.search-box input {
  width: 100%;
  padding: 10px 16px 10px 40px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 14px;
  background: #F5F5F7;
  transition: all 0.2s;
}

.search-box input:focus {
  outline: none;
  background: white;
  border-color: #7C3AED;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #8E8E93;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.btn-secondary {
  background: #F5F5F7;
  color: #1D1D1F;
}

.btn-secondary:hover {
  background: #E5E5EA;
}

.btn-danger {
  background: #FFF0EF;
  color: #FF3B30;
}

.btn-danger:hover {
  background: #FFE5E3;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.strategy-section {
  margin-bottom: 24px;
}

.strategy-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(124, 58, 237, 0.1);
}

.strategy-name {
  font-size: 16px;
  font-weight: 700;
  color: #7C3AED;
}

.strategy-count {
  font-size: 13px;
  color: #8E8E93;
  background: #F5F5F7;
  padding: 2px 10px;
  border-radius: 12px;
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-row {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.product-row:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-color: rgba(124, 58, 237, 0.3);
}

.product-row-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
}

.product-basic-info {
  flex: 1;
}

.product-row-name {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.product-row-code {
  font-family: "SF Mono", "Menlo", monospace;
  font-size: 12px;
  color: #7C3AED;
  font-weight: 600;
  background: rgba(124, 58, 237, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}

.product-row-info {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #6E6E73;
}

.product-row-info span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.risk-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

.risk-r3 {
  background: #E3F5E8;
  color: #1A9E3F;
}

.risk-r4 {
  background: #FFF4E0;
  color: #FF9500;
}

.risk-r5 {
  background: #FFF0EF;
  color: #FF3B30;
}

.coefficient-box {
  width: 100px;
  text-align: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border-radius: 10px;
  border: 1px solid rgba(124, 58, 237, 0.2);
}

.coefficient-box-label {
  font-size: 11px;
  color: #8E8E93;
  margin-bottom: 2px;
}

.coefficient-box-value {
  font-size: 20px;
  font-weight: 700;
  color: #7C3AED;
}

.product-row-actions {
  display: flex;
  gap: 8px;
}

.product-detail-panel {
  display: none;
  background: #FAFAFB;
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 12px;
  padding: 20px;
  margin-top: -6px;
  margin-bottom: 6px;
}

.product-detail-panel.active {
  display: block;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.detail-item {
  background: white;
  padding: 12px 14px;
  border-radius: 8px;
}

.detail-label {
  font-size: 11px;
  color: #8E8E93;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
  color: #1D1D1F;
}
</style>
