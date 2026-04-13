# 投资顾问服务实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans

**Goal:** 在 FinTrack 系统中实现投资顾问服务订阅跟踪功能

**Architecture:** 后端 FastAPI + SQLAlchemy，前端 Vue3，数据时点更新机制

**Tech Stack:** FastAPI, SQLAlchemy, Vue3, Element Plus, ECharts

---

## 文件结构

### 后端
- `backend/app/models/advisory.py` - 数据模型
- `backend/app/routers/advisory.py` - API路由  
- `backend/app/schemas/advisory.py` - Pydantic schemas

### 前端
- `frontend/src/views/AdvisoryService.vue` - 主页面
- `frontend/src/components/advisory/*.vue` - 子组件
- `frontend/src/api/advisory.js` - API接口

---

## Task 1: 后端数据模型

**Files:**
- Create: `backend/app/models/advisory.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建投顾签约记录模型**

```python
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class InvestmentAdvisorySubscription(Base):
    __tablename__ = "investment_advisory_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    product_type = Column(String(20), nullable=False)
    subscription_date = Column(Date, nullable=False)
    asset_amount = Column(Numeric(15, 2), nullable=False)
    advisory_income = Column(Numeric(15, 2), nullable=False)
    original_households = Column(Integer, default=1)
    converted_households = Column(Integer, default=1)
    conversion_note = Column(String(255))
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    member = relationship("Member")
    group = relationship("Group")

class InvestmentAdvisoryTarget(Base):
    __tablename__ = "investment_advisory_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    year = Column(Integer, nullable=False)
    income_target = Column(Numeric(15, 2), default=0)
    households_target = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    group = relationship("Group")
```

- [ ] **Step 2: 在 models/__init__.py 导入模型并 Commit**

---

## Task 2: 后端 API 路由

**Files:**
- Create: `backend/app/routers/advisory.py`
- Modify: `backend/app/main.py`

主要端点:
- GET /api/advisory/stats - 统计数据
- GET /api/advisory/subscriptions - 签约明细
- POST /api/advisory/subscriptions/import - 数据导入
- PUT /api/advisory/subscriptions/{id} - 更新折算户数
- GET /api/advisory/targets - 考核指标
- POST /api/advisory/targets - 设置指标

---

## Task 3: 前端 API 接口

**Files:**
- Create: `frontend/src/api/advisory.js`

---

## Task 4: 前端主页面

**Files:**
- Create: `frontend/src/views/AdvisoryService.vue`
- Modify: `frontend/src/router/index.js` 或菜单配置

---

## Task 5: 年度看板组件

**Files:**
- Create: `frontend/src/components/advisory/AdvisoryDashboard.vue`

包含:
- KPICards 组件
- ProductDistribution 组件
- TrendChart 组件

---

## Task 6: 营业部视图组件

**Files:**
- Create: `frontend/src/components/advisory/AdvisoryGroupView.vue`

---

## Task 7: 个人视图组件

**Files:**
- Create: `frontend/src/components/advisory/AdvisoryMemberView.vue`

---

## Task 8: 数据导入组件

**Files:**
- Create: `frontend/src/components/advisory/AdvisoryImport.vue`

---

## Task 9: 考核管理组件

**Files:**
- Create: `frontend/src/components/advisory/AdvisoryTarget.vue`

---

## 执行方式

**Plan complete.** 设计文档和计划框架已保存。

**Two execution options:**

1. **Subagent-Driven (recommended)** - 每个任务派生子代理执行，我负责审查
2. **Inline Execution** - 在当前会话批量执行任务

**Which approach would you prefer?**
