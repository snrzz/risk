# OpenClaw on FNOS 部署手册

## 概述

本手册介绍如何在FNOS（FreeNAS/TrueNAS的操作系统）上部署OpenClaw（Clawdbot），实现：
- 微信/WhatsApp等消息通道对接
- 本地大模型支持（Ollama）
- Docker容器化部署
- Web UI管理界面

## 环境要求

### FNOS版本
- TrueNAS CORE 13.0+
- TrueNAS SCALE 22.12+ (推荐)

### 系统资源
- CPU: 4核+
- 内存: 8GB+
- 存储: 50GB+ (Jail/iocage容器空间)

### 网络要求
- 固定IP地址
- 开放端口: 18789 (Web UI), 11434 (Ollama)
- 互联网访问（用于GitHub/Docker Hub）

## 第一步：准备工作

### 1.1 启用Jail/iocage（TrueNAS CORE）

```bash
# SSH登录TrueNAS
ssh admin@truenas-ip

# 创建Jail
iocage create -n openclaw -r 13.3-RELEASE ip4_addr="lo1|192.168.1.100/24" defaultrouter="192.168.1.1" vnet="on" allow_raw_sockets="1" boot="on"

# 进入Jail
iocage console openclaw
```

### 1.2 配置TrueNAS SCALE（使用Docker）

```bash
# 在TrueNAS SCALE Web界面中
# 1. 进入Apps → Settings → Advanced
# 2. 启用Docker
# 3. 创建存储池用于应用
```

### 1.3 安装基础依赖

```bash
# 在Jail/容器内执行
pkg update && pkg upgrade -y
pkg install -y curl git nano wget

# 安装Python 3.11
pkg install -y python311 py311-pip py311-venv

# 安装Node.js 22
curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz | tar -xJ -C /usr/local --strip-components=1

# 验证安装
node --version  # 应显示 v22.12.0
npm --version
python3 --version  # 应显示 3.11.x
```

## 第二步：安装Docker（TrueNAS SCALE跳过此步）

```bash
# FreeBSD Jail安装Docker
pkg install -y docker-ce docker-compose

# 启用服务
sysrc docker_enable="YES"
service docker start

# 当前会话加入docker组
pw groupmod docker -m username || pw groupadd -n docker -M username
```

## 第三步：部署Ollama（本地大模型）

### 3.1 安装Ollama

```bash
# Linux/TrueNAS SCALE
curl -fsSL https://ollama.ai/install.sh | sh

# 启动Ollama服务
systemctl enable ollama
systemctl start ollama

# 验证
curl http://localhost:11434/api/version
```

### 3.2 下载模型

```bash
# 下载推荐模型（根据显存/内存选择）
# 7B模型：需要4GB+显存/8GB+内存
ollama pull llama3.2

# 中文模型
ollama pull qwen2.5:7b

# 代码模型（可选）
ollama pull deepseek-coder:7b

# 查看已下载模型
ollama list
```

### 3.3 配置GPU（如有NVIDIA显卡）

```bash
# TrueNAS SCALE启用GPU直通
# Web界面 → Apps → 设置 → Resources → 添加GPU

# 验证GPU识别
nvidia-smi
```

## 第四步：部署OpenClaw（Clawdbot）

### 4.1 克隆代码

```bash
mkdir -p /mnt/volume1/appdata
cd /mnt/volume1/appdata
git clone https://github.com/clawdbot/clawdbot.git
cd clawdbot
```

### 4.2 配置环境

```bash
# 创建环境变量文件
cat > .env << EOF
# JWT配置
CLAWDBOT_JWT_SECRET_KEY=your-secret-key-change-this

# Ollama配置（本地大模型）
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2

# 端口配置
CLAWDBOT_PORT=18789
CLAWDBOT_HOST=0.0.0.0

# 数据目录
CLAWDBOT_DATA=/mnt/volume1/appdata/clawd
EOF

# 创建数据目录
mkdir -p /mnt/volume1/appdata/clawd
```

### 4.3 首次运行

```bash
# 使用Docker运行
docker run -d \
  --name clawdbot \
  -p 18789:18789 \
  -p 11434:11434 \
  -v /mnt/volume1/appdata/clawd:/root/.clawdbot \
  -v /mnt/volume1/appdata/clawdbot:/app \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --restart unless-stopped \
  clawdbot/clawdbot:latest

# 或使用本地运行
npm install -g pnpm
pnpm install
pnpm dev
```

### 4.4 首次配置向导

首次运行会提示配置：

```
? What's your name? → 输入你的名字
? How should I address you? → 输入称呼
? Select your interface: → 选择 Control UI (Web)
? Choose your primary model provider: → 选择 Ollama
? Enter the base URL of your Ollama server: → http://localhost:11434
```

## 第五步：配置通道

### 5.1 WhatsApp配置

```bash
# 进入容器
docker exec -it clawdbot bash

# 扫码登录
clawdbot channels login --channel whatsapp

# 扫描显示的QR码
```

### 5.2 Telegram配置

```bash
# 1. 联系 @BotFather 获取Token
# 2. 配置Token
clawdbot channels add --channel telegram --token "your-bot-token"
```

### 5.3 微信配置（需要证书）

```bash
# 导出证书后配置
clawdbot channels add --channel wechat --cert /path/to/cert.pem
```

## 第六步：TrueNAS SCALE 应用配置

### 6.1 创建应用

```yaml
# TrueNAS SCALE ix-volume配置
# 添加以下存储卷:
# - /mnt/volume1/appdata/clawd:/root/.clawdbot
# - /mnt/volume1/appdata/clawdbot:/app

# 添加端口映射:
# - 18789:18789
# - 11434:11434

# 环境变量:
# OLLAMA_BASE_URL=http://host.docker.internal:11434
# DEFAULT_MODEL=llama3.2
```

### 6.2 GPU直通（可选）

```yaml
# GPU配置（在TrueNAS SCALE UI中配置）
resources:
  gpu:
    nvidia:
      - 0  # GPU设备号
```

## 第七步：验证部署

### 7.1 检查服务状态

```bash
# 检查Ollama
curl http://localhost:11434/api/tags

# 检查Clawdbot
curl http://localhost:18789/api/health

# 查看日志
docker logs clawdbot -f
```

### 7.2 访问Web UI

```
打开浏览器访问: http://truenas-ip:18789
```

### 7.3 测试消息发送

```bash
# 测试API
curl -X POST http://localhost:18789/api/agents/main/message \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，测试一下"}'
```

## 第八步：系统优化

### 8.1 配置systemd服务

```bash
# 创建systemd服务文件
cat > /etc/systemd/system/clawdbot.service << EOF
[Unit]
Description=Clawdbot Service
After=network.target ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/mnt/volume1/appdata/clawdbot
ExecStart=/mnt/volume1/appdata/clawdbot/venv/bin/python -m gunicorn risk_project.wsgi:application --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
systemctl enable clawdbot
systemctl start clawdbot
```

### 8.2 配置Nginx反向代理

```nginx
# /usr/local/etc/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream clawdbot {
        server 127.0.0.1:8000;
    }

    server {
        listen 80;
        server_name truenas.local;

        location / {
            proxy_pass http://clawdbot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### 8.3 SSL配置（Let's Encrypt）

```bash
# 安装certbot
pkg install -y py311-certbot

# 获取证书
certbot certonly --standalone -d your-domain.com

# 配置HTTPS重定向
```

## 第九步：备份与恢复

### 9.1 备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/mnt/volume1/backups/clawdbot

# 备份数据目录
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /mnt/volume1/appdata/clawd

# 备份Docker镜像
docker save clawdbot/clawdbot:latest | gzip > $BACKUP_DIR/clawdbot_$DATE.tar.gz

# 备份Ollama模型
tar -czf $BACKUP_DIR/ollama_models_$DATE.tar.gz /root/.ollama

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 9.2 恢复步骤

```bash
# 恢复数据
tar -xzf /mnt/volume1/backups/clawdbot/data_20250117.tar.gz -C /

# 恢复Docker镜像
docker load < /mnt/volume1/backups/clawdbot/clawdbot_20250117.tar.gz

# 重启服务
docker-compose restart
```

## 常见问题排查

### 问题1：Ollama无法启动
```bash
# 检查端口占用
netstat -tulpn | grep 11434

# 检查GPU驱动
nvidia-smi

# 查看日志
journalctl -u ollama -f
```

### 问题2：Clawdbot连接Ollama失败
```bash
# 检查Ollama服务状态
curl http://localhost:11434/api/tags

# 检查环境变量
env | grep OLLAMA

# 重启Clawdbot容器
docker restart clawdbot
```

### 问题3：微信无法登录
```bash
# 检查证书有效性
openssl x509 -in /path/to/cert.pem -noout -dates

# 检查iOS版本兼容性
# Clawdbot需要iOS 16.1+
```

### 问题4：内存不足
```bash
# 使用更小的模型
ollama pull llama3.2:3b

# 或使用量化模型
ollama pull llama3.2:latest
```

## 性能调优

### Ollama优化

```bash
# 设置GPU层数（根据显存调整）
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_GPU_LAYERS=35

# 设置并发数
export OLLAMA_NUM_PARALLEL=4
```

### Clawdbot优化

```python
# config.py
AGENT_CONFIG = {
    'max_tokens': 4096,
    'temperature': 0.7,
    'context_window': 32768,
}
```

## 联系支持

- GitHub Issues: https://github.com/clawdbot/clawdbot/issues
- 文档: https://docs.clawd.bot
- Discord: https://discord.gg/clawd

## 更新日志

| 日期 | 版本 | 更新内容 |
|-----|------|---------|
| 2025-01-17 | 1.0 | 初版文档 |
