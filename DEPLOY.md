# FinTrack Render 部署指南

## 前置要求
1. 代码已推送到 GitHub 仓库
2. 拥有 Render 账号 (https://render.com)

## 部署步骤

### 第一步：推送代码到 GitHub

```bash
# 如果没有远程仓库，先创建
git remote add origin https://github.com/你的用户名/fintrack.git

# 提交所有更改
git add .
git commit -m "准备 Render 部署"

# 推送到 GitHub
git push -u origin main
```

### 第二步：在 Render 部署后端

1. 登录 https://dashboard.render.com
2. 点击 "New +" → "Blueprint"
3. 选择你的 GitHub 仓库
4. 点击 "Apply"，Render 会自动读取 `render.yaml`

**注意**：先只部署后端服务 `fintrack-api`

### 第三步：部署前端

后端部署完成后（状态变为 Live）：

1. 在 Render Dashboard 点击 "New +" → "Static Site"
2. 选择同一个 GitHub 仓库
3. 配置如下：
   - **Name**: fintrack-web
   - **Build Command**:
     ```
     cd frontend && echo "VITE_API_BASE_URL=https://fintrack-api.onrender.com" > .env.production && npm install && npm run build
     ```
   - **Publish Directory**: frontend/dist
4. 点击 "Create Static Site"

### 第四步：验证部署

- 后端地址：https://fintrack-api.onrender.com
- 前端地址：https://fintrack-web.onrender.com

访问前端地址即可看到应用。

## 注意事项

1. **免费版限制**：15分钟无访问会自动休眠，首次访问需等待30秒唤醒
2. **数据持久化**：SQLite 数据已配置持久化磁盘，重启不会丢失
3. **如需更新代码**：推送到 GitHub 后，Render 会自动重新部署

## 自定义域名（可选）

在 Render Dashboard 中可以为服务绑定自己的域名。
