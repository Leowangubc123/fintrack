# FinTrack - 金融产品销量追踪系统

基于 Apple Design System 设计的金融产品销量追踪系统。

## 功能特性

- **数据看板**: KPI 卡片、在售产品明细、营业部完成情况、大单提醒、预警信息
- **营销人员管理**: 营业部管理、成员管理、转组功能
- **产品管理**: 产品列表、状态追踪、归档功能
- **数据导入**: 5 步 Excel 导入向导
- **数据分析**: 个人分析、产品矩阵、营业部对比

## 技术栈

**后端**
- Python 3.11 + FastAPI
- SQLAlchemy ORM
- SQLite 数据库
- Pydantic 数据验证

**前端**
- Vue 3 + Vite
- Element Plus UI 组件库
- Apple Design System 设计

**部署**
- Docker + Docker Compose
- Nginx 反向代理

## 快速开始

### 方法一：Docker 部署（推荐）

```bash
cd /Users/leowang/FinTrack

# 启动所有服务
docker-compose up --build

# 后台运行
docker-compose up -d --build
```

访问地址：
- 前端页面：http://localhost:8080
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

停止服务：
```bash
docker-compose down
```

### 方法二：本地开发

**1. 启动后端**

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

**2. 启动前端**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问地址：
- 前端页面：http://localhost:5173
- 后端 API：http://localhost:8000

## 项目结构

```
FinTrack/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── main.py       # FastAPI 入口
│   │   ├── models/       # 数据库模型
│   │   ├── routers/      # API 路由
│   │   ├── schemas/      # Pydantic 模型
│   │   └── database.py   # 数据库配置
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── layouts/      # 布局组件
│   │   ├── api/          # API 接口
│   │   └── router/       # 路由配置
│   ├── Dockerfile
│   └── nginx.conf        # Nginx 配置
├── docker-compose.yml    # Docker Compose 配置
└── README.md
```

## Apple 设计风格

- **玻璃拟态**: 侧边栏和顶部导航使用 backdrop-filter 模糊效果
- **圆角设计**: 16px 大圆角卡片，10px 按钮圆角
- **配色方案**:
  - 主色: #007AFF (蓝色)
  - 成功: #34C759 (绿色)
  - 警告: #FF9500 (橙色)
  - 危险: #FF3B30 (红色)
  - 背景: #F5F5F7
  - 文字: #1D1D1F (主), #6E6E73 (次)
- **阴影**: 柔和的 4px 20px 阴影效果
- **过渡动画**: 0.2s ease 平滑过渡

## API 接口

### 组织架构
- `GET/POST /api/groups` - 营业部列表/创建
- `PUT/DELETE /api/groups/{id}` - 更新/删除营业部
- `GET/POST /api/members` - 成员列表/创建
- `PUT/DELETE /api/members/{id}` - 更新/删除成员
- `POST /api/members/{id}/transfer` - 成员转组

### 产品管理
- `GET/POST /api/products` - 产品列表/创建
- `PUT/DELETE /api/products/{id}` - 更新/删除产品
- `POST /api/products/{id}/archive` - 归档产品

### 数据导入
- `POST /api/import/preview` - 预览导入数据
- `POST /api/import/execute` - 执行导入

### 数据看板
- `GET /api/dashboard/summary` - 汇总数据
- `GET /api/dashboard/products` - 在售产品
- `GET /api/dashboard/groups-ranking` - 营业部排名
- `GET /api/dashboard/matrix` - 产品矩阵
- `GET /api/dashboard/large-orders` - 大单数据

## 数据模型

- **Group**: 营业部
- **Member**: 营销人员
- **Product**: 金融产品
- **SalesRecord**: 销售记录
- **ImportLog**: 导入日志

## 注意事项

1. 删除营业部前需要先删除或转移其下的成员
2. 删除成员前需要确认其没有销售记录
3. 删除产品前需要确认其没有销售记录
4. 数据导入支持 .xlsx, .xls, .csv 格式

## 开发计划

查看 [docs/plans/2026-03-08-fintracks-implementation.md](docs/plans/2026-03-08-fintracks-implementation.md) 了解详细开发计划。

## License

MIT
