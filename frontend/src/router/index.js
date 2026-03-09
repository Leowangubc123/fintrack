import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import Organization from '../views/Organization.vue'
import Products from '../views/Products.vue'
import Import from '../views/Import.vue'
import Analysis from '../views/Analysis.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'Dashboard', component: Dashboard, meta: { title: '数据看板' } },
      { path: 'organization', name: 'Organization', component: Organization, meta: { title: '营销人员' } },
      { path: 'products', name: 'Products', component: Products, meta: { title: '产品管理' } },
      { path: 'import', name: 'Import', component: Import, meta: { title: '数据导入' } },
      { path: 'analysis', name: 'Analysis', component: Analysis, meta: { title: '数据分析' } },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
