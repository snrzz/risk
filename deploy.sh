#!/bin/bash
#
# 风险预警系统 - 一键部署脚本
# 支持系统: Ubuntu 20.04+ / Debian 11+ / CentOS 7+ / TrueNAS SCALE
#
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_DIR="/opt/risk-system"
DATA_DIR="/data/risk"
BACKUP_DIR="/backup/risk"
LOG_FILE="/var/log/risk-deploy.log"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            log_info "检测到系统: $PRETTY_NAME"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_warn "macOS系统，部分功能可能受限"
    else
        log_warn "未知系统类型: $OSTYPE"
    fi
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_info "Python版本: $PYTHON_VERSION"
    else
        log_error "未检测到Python3，请先安装Python 3.11+"
        exit 1
    fi
    
    # 检查Docker
    if command -v docker &> /dev/null; then
        log_info "Docker已安装: $(docker --version)"
    else
        log_warn "Docker未安装，将使用本地模式"
    fi
}

# 安装依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y curl git wget nginx
    elif command -v yum &> /dev/null; then
        sudo yum install -y curl git wget nginx
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y curl git wget nginx
    fi
    
    log_info "系统依赖安装完成"
}

# 安装Python环境
install_python() {
    log_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "请先安装Python 3.11+"
        exit 1
    fi
    
    # 安装pip
    if ! command -v pip3 &> /dev/null; then
        log_info "安装pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3
    fi
    
    # 创建虚拟环境
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv "$PROJECT_DIR/venv"
    fi
    
    # 激活虚拟环境
    source "$PROJECT_DIR/venv/bin/activate"
    
    # 升级pip
    pip install -q --upgrade pip
    
    log_info "Python环境准备完成"
}

# 部署项目
deploy_project() {
    log_info "部署项目..."
    
    # 创建目录
    sudo mkdir -p "$PROJECT_DIR"
    sudo mkdir -p "$DATA_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "$(dirname $LOG_FILE)"
    sudo touch "$LOG_FILE"
    sudo chmod 777 "$LOG_FILE"
    
    # 克隆项目
    if [ -d "$PROJECT_DIR/.git" ]; then
        log_info "更新现有项目..."
        cd "$PROJECT_DIR"
        git pull origin main
    else
        log_info "克隆项目..."
        sudo git clone https://github.com/snrzz/risk.git "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    # 复制数据目录
    sudo cp -r data_template/* "$DATA_DIR/" 2>/dev/null || true
    
    log_info "项目部署完成"
}

# 配置项目
configure_project() {
    log_info "配置项目..."
    
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    
    # 创建环境变量文件
    cat > "$PROJECT_DIR/.env" << EOF
# 风险预警系统配置
DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 数据库配置（使用SQLite用于快速测试）
DATABASE_URL=sqlite:///$(echo $DATA_DIR | sed 's/\//\\\//g')/risk.db

# Redis配置（可选）
# REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# 日志配置
LOG_LEVEL=INFO

# 端口配置
PORT=8000
HOST=0.0.0.0
EOF
    
    log_info "配置文件已生成: $PROJECT_DIR/.env"
}

# 安装Python依赖
install_requirements() {
    log_info "安装Python依赖..."
    
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    
    pip install -q -r requirements.txt
    
    log_info "Python依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    
    # 执行迁移
    python manage.py makemigrations accounts risk tasks --noinput
    python manage.py migrate
    
    # 创建管理员账户
    python manage.py shell -c "
from accounts.models import User, Role, Permission
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'Admin123!@#')
    print('管理员账户已创建: admin@example.com / Admin123!@#')
"
    
    # 初始化权限数据
    python manage.py shell -c "
from accounts.models import Permission, Role
permissions_data = [
    ('用户管理', 'user_manage', 'user', 'manage'),
    ('角色管理', 'role_manage', 'role', 'manage'),
    ('组合管理', 'portfolio_manage', 'portfolio', 'manage'),
    ('交易查看', 'trade_read', 'trade', 'read'),
    ('风险查看', 'risk_read', 'risk', 'read'),
    ('预警处理', 'alert_manage', 'alert', 'manage'),
    ('任务管理', 'task_manage', 'task', 'manage'),
]
for name, code, resource, action in permissions_data:
    Permission.objects.get_or_create(code=code, defaults={
        'name': name, 'resource_type': resource, 'action_type': action
    })
print('权限初始化完成')
"
    
    log_info "数据库初始化完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端..."
    
    cd "$PROJECT_DIR/frontend"
    
    # 安装Node依赖
    npm install --legacy-peer-deps --quiet
    
    # 构建
    npm run build
    
    log_info "前端构建完成"
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx..."
    
    # 备份原配置
    if [ -f /etc/nginx/nginx.conf ]; then
        sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
    fi
    
    # 生成配置
    sudo cat > /etc/nginx/conf.d/risk.conf << EOF
upstream risk_backend {
    server 127.0.0.1:8000;
}

upstream risk_frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name localhost;

    # 前端静态文件
    location / {
        proxy_pass http://risk_frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API代理
    location /api/ {
        proxy_pass http://risk_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 健康检查
    location /health {
        proxy_pass http://risk_backend;
    }
}
EOF
    
    # 测试配置
    sudo nginx -t
    
    # 重启Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log_info "Nginx配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    
    # 启动后端服务（生产模式）
    nohup python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
    
    # 启动前端服务
    cd frontend
    nohup npm run dev -- --host 0.0.0.0 > /dev/null 2>&1 &
    
    log_info "服务已启动"
}

# 创建systemd服务
create_services() {
    log_info "创建systemd服务..."
    
    # 后端服务
    sudo cat > /etc/systemd/system/risk-backend.service << EOF
[Unit]
Description=Risk Warning System Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 前端服务
    sudo cat > /etc/systemd/system/risk-frontend.service << EOF
[Unit]
Description=Risk Warning System Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/frontend
ExecStart=/usr/bin/npx vite --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable risk-backend risk-frontend
    
    log_info "systemd服务已创建"
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    # 检查进程
    if pgrep -f "manage.py runserver" > /dev/null; then
        log_info "后端服务运行正常"
    else
        log_warn "后端服务未运行"
    fi
    
    if pgrep -f "vite" > /dev/null; then
        log_info "前端服务运行正常"
    else
        log_warn "前端服务未运行"
    fi
    
    # 检查端口
    if command -v ss &> /dev/null; then
        ss -tlnp | grep -E '(8000|3000|80)' && log_info "端口监听正常"
    fi
    
    # 测试API
    sleep 2
    if curl -s http://localhost:8000/api/risk/dashboard/ > /dev/null; then
        log_info "API访问正常"
    else
        log_warn "API访问异常，请检查日志"
    fi
    
    # 测试前端
    if curl -s http://localhost:3000 > /dev/null; then
        log_info "前端访问正常"
    else
        log_warn "前端访问异常"
    fi
}

# 打印部署信息
print_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   风险预警系统部署完成！${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "  ${GREEN}Web UI:${NC}     http://localhost:3000"
    echo -e "  ${GREEN}API地址:${NC}    http://localhost:8000"
    echo -e "  ${GREEN}文档:${NC}      http://localhost:8000/api/docs/"
    echo ""
    echo -e "  ${YELLOW}默认登录:${NC}"
    echo -e "    邮箱:    admin@example.com"
    echo -e "    密码:    Admin123!@#"
    echo ""
    echo -e "  ${YELLOW}常用命令:${NC}"
    echo -e "    查看日志:  tail -f $LOG_FILE"
    echo -e "    重启服务:  sudo systemctl restart risk-backend risk-frontend"
    echo -e "    停止服务:  sudo systemctl stop risk-backend risk-frontend"
    echo ""
    echo -e "  ${YELLOW}部署文档:${NC}"
    echo -e "    $PROJECT_DIR/docs/DEPLOYMENT.md"
    echo ""
    echo -e "${BLUE}========================================${NC}"
}

# 主函数
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   风险预警系统 - 一键部署脚本${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_system
    install_dependencies
    install_python
    deploy_project
    configure_project
    install_requirements
    init_database
    build_frontend
    configure_nginx
    create_services
    start_services
    verify_deployment
    print_summary
}

# 执行主函数
main "$@"
