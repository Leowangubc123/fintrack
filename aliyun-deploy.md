# FinTrack 阿里云轻量服务器部署指南

## 服务器要求

- **配置**: 1核2G 或 2核2G（70元/年款）
- **系统**: Ubuntu 22.04 LTS
- **带宽**: 3Mbps+
- **磁盘**: 40GB SSD

---

## 部署步骤

### 第一步：购买并初始化服务器

1. 登录阿里云控制台
2. 购买轻量应用服务器（70元/年套餐）
3. 选择系统镜像：**Ubuntu 22.04 LTS**
4. 设置 root 密码
5. 记录服务器公网 IP

### 第二步：连接服务器

```bash
# Mac/Linux 终端
ssh root@你的服务器IP

# Windows 使用 PowerShell 或 Git Bash
ssh root@你的服务器IP
```

### 第三步：一键部署

在服务器上执行：

```bash
# 1. 下载部署脚本
cd /root
wget https://raw.githubusercontent.com/Leowangubc123/fintrack/main/deploy/aliyun-setup.sh

# 2. 执行部署
chmod +x aliyun-setup.sh
./aliyun-setup.sh
```

或手动执行（见下文详细步骤）

---

## 手动部署详细步骤

### 1. 更新系统并安装依赖

```bash
apt update && apt upgrade -y
apt install -y python3-pip python3-venv nodejs npm nginx git
```

### 2. 上传项目代码

**本地电脑执行：**
```bash
cd /Users/leowang/FinTrack
scp -r . root@你的服务器IP:/opt/fintrack
```

或从 GitHub 克隆：
```bash
cd /opt
git clone https://github.com/Leowangubc123/fintrack.git
```

### 3. 配置后端

```bash
cd /opt/fintrack/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 -c "from app.database import engine, Base; from app.models import group, member, product, sales; Base.metadata.create_all(bind=engine)"
```

### 4. 配置前端

```bash
cd /opt/fintrack/frontend

# 安装依赖
npm install

# 构建（使用生产环境 API 地址）
echo "VITE_API_BASE_URL=http://你的服务器IP:8000" > .env.production
npm run build
```

### 5. 配置 Nginx

创建配置文件：

```bash
cat > /etc/nginx/sites-available/fintrack << 'EOF'
server {
    listen 80;
    server_name _;  # 接受所有域名

    # 前端静态文件
    location / {
        root /opt/fintrack/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/fintrack /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试并重载
nginx -t
systemctl reload nginx
```

### 6. 配置后端服务（systemd）

```bash
cat > /etc/systemd/system/fintrack-api.service << 'EOF'
[Unit]
Description=FinTrack API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fintrack/backend
Environment="PATH=/opt/fintrack/backend/venv/bin"
Environment="DATABASE_URL=sqlite:///./fintrack.db"
Environment="ALLOWED_ORIGINS=*"
ExecStart=/opt/fintrack/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable fintrack-api
systemctl start fintrack-api
```

### 7. 开放防火墙

```bash
# 开放 HTTP (80) 端口
ufw allow 80/tcp
ufw allow 22/tcp
ufw --force enable

# 阿里云控制台也需要开放端口
# 登录阿里云控制台 -> 轻量服务器 -> 防火墙 -> 添加规则
```

---

## 访问应用

部署完成后，通过服务器 IP 访问：

```
http://你的服务器IP
```

---

## 常用维护命令

```bash
# 查看后端状态
systemctl status fintrack-api

# 重启后端
systemctl restart fintrack-api

# 查看后端日志
journalctl -u fintrack-api -f

# 重启 Nginx
systemctl restart nginx

# 查看 Nginx 日志
tail -f /var/log/nginx/error.log
```

---

## 数据备份

```bash
# 备份数据库
cp /opt/fintrack/backend/fintrack.db /opt/fintrack/backup/fintrack-$(date +%Y%m%d).db

# 下载到本地（本地执行）
scp root@你的服务器IP:/opt/fintrack/backup/fintrack-20240115.db .
```

---

## 备案说明

- **必须备案**：使用国内服务器 + 域名访问
- **备案期间**：可使用 IP 地址访问
- **备案流程**：阿里云控制台 -> ICP备案 -> 按指引提交资料
- **备案时间**：约 7-20 个工作日
