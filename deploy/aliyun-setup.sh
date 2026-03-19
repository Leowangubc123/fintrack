#!/bin/bash

# FinTrack 阿里云一键部署脚本
# 使用方法: ./aliyun-setup.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "   FinTrack 阿里云部署脚本"
echo "=========================================="

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me)
echo "服务器 IP: $SERVER_IP"

# 1. 更新系统
echo "[1/8] 更新系统..."
apt update && apt upgrade -y

# 2. 安装依赖
echo "[2/8] 安装 Python、Node.js、Nginx..."
apt install -y python3-pip python3-venv nodejs npm nginx git curl

# 3. 克隆项目
echo "[3/8] 下载 FinTrack 项目..."
if [ ! -d "/opt/fintrack" ]; then
    cd /opt
    git clone https://github.com/Leowangubc123/fintrack.git
else
    echo "项目已存在，更新代码..."
    cd /opt/fintrack
    git pull
fi

# 4. 配置后端
echo "[4/8] 配置后端服务..."
cd /opt/fintrack/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/fintrack/backend')
from app.database import engine, Base
from app.models import group, member, product, sales
Base.metadata.create_all(bind=engine)
print("数据库初始化完成")
PYTHON_EOF

# 5. 配置前端
echo "[5/8] 构建前端..."
cd /opt/fintrack/frontend

# 安装依赖
npm install

# 构建（使用服务器 IP 作为 API 地址）
echo "VITE_API_BASE_URL=http://$SERVER_IP:8000" > .env.production
npm run build

# 6. 配置 Nginx
echo "[6/8] 配置 Nginx..."
cat > /etc/nginx/sites-available/fintrack << NGINX_EOF
server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root /opt/fintrack/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
    }
}
NGINX_EOF

# 启用配置
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/fintrack /etc/nginx/sites-enabled/

# 测试并重载
nginx -t && systemctl reload nginx

# 7. 配置 systemd 服务
echo "[7/8] 配置后端服务..."
cat > /etc/systemd/system/fintrack-api.service << SERVICE_EOF
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
SERVICE_EOF

# 启动服务
systemctl daemon-reload
systemctl enable fintrack-api
systemctl start fintrack-api

# 8. 配置防火墙
echo "[8/8] 配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw --force enable

echo ""
echo "=========================================="
echo "   部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://$SERVER_IP"
echo ""
echo "常用命令:"
echo "  查看后端状态: systemctl status fintrack-api"
echo "  重启后端: systemctl restart fintrack-api"
echo "  查看日志: journalctl -u fintrack-api -f"
echo "  重启 Nginx: systemctl restart nginx"
echo ""
echo "注意：如果无法访问，请在阿里云控制台开放 80 端口"
echo "      轻量服务器 -> 防火墙 -> 添加规则 -> HTTP (80)"
echo ""
