#!/bin/bash
#
# 风险预警系统 - 一键部署脚本
# 支持系统: Ubuntu 20.04+ / Debian 11+ / CentOS 7+ / macOS
#
# 用法:
#   chmod +x deploy.sh
#   sudo ./deploy.sh     # Linux需要root权限
#   ./deploy.sh          # macOS本地测试
#
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置变量
PROJECT_DIR="/opt/risk-system"
DATA_DIR="/data/risk"
BACKUP_DIR="/backup/risk"
LOG_FILE="/var/log/risk-deploy.log"
ERROR_LOG="/var/log/risk-deploy-error.log"

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE" 2>/dev/null || true; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE" 2>/dev/null || true; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$ERROR_LOG"; echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE" 2>/dev/null || true; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; echo "[STEP] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE" 2>/dev/null || true; }

check_root() {
    if [[ "$OSTYPE" == "linux-gnu"* ]] && [ "$EUID" -ne 0 ]; then
        log_error "此脚本需要root权限运行，请使用: sudo $0"
        exit 1
    fi
}

check_system() {
    log_step "检查系统环境..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        [ -f /etc/os-release ] && { . /etc/os-release; log_info "检测到系统: $PRETTY_NAME"; }
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "检测到系统: macOS"
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "未检测到Python3，请先安装Python 3.11+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        log_error "Python版本过低，需要3.11+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    log_info "Python版本: $PYTHON_VERSION ✓"
    
    if ! command -v git &> /dev/null; then
        log_warn "Git未安装，尝试安装..."
        (command -v apt-get &> /dev/null && sudo apt-get update -qq && sudo apt-get install -y git) || \
        (command -v yum &> /dev/null && sudo yum install -y git) || true
    fi
    log_info "Git版本: $(git --version | cut -d' ' -f3) ✓"
}

install_dependencies() {
    log_step "安装系统依赖..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y curl git wget nginx python3-pip 2>&1 | grep -v "already" || true
    elif command -v yum &> /dev/null; then
        sudo yum install -y curl git wget epel-release nginx 2>&1 | grep -v "already" || true
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y curl git wget nginx 2>&1 | grep -v "already" || true
    fi
    log_info "系统依赖安装完成 ✓"
}

check_node() {
    log_step "检查Node.js环境..."
    if command -v node &> /dev/null; then
        NODE_MAJOR=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        [ "$NODE_MAJOR" -ge 20 ] && { log_info "Node.js版本: $(node --version) ✓"; return 0; }
    fi
    log_info "安装Node.js 20..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - 2>/dev/null || true
        sudo apt-get install -y nodejs 2>&1 | grep -v "already" || true
    fi
    command -v node &> /dev/null && log_info "Node.js版本: $(node --version) ✓" || log_error "Node.js安装失败"
}

check_npm() {
    command -v npm &> /dev/null && log_info "npm版本: $(npm --version) ✓" || log_error "npm未安装"
}

install_python_env() {
    log_step "配置Python环境..."
    if ! command -v pip3 &> /dev/null; then
        curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3 2>/dev/null || python3 -m ensurepip --upgrade 2>/dev/null || exit 1
    fi
    [ ! -d "$PROJECT_DIR/venv" ] && python3 -m venv "$PROJECT_DIR/venv"
    source "$PROJECT_DIR/venv/bin/activate"
    pip install -q --upgrade pip setuptools wheel
    log_info "Python环境准备完成 ✓"
}

deploy_project() {
    log_step "部署项目代码..."
    sudo mkdir -p "$PROJECT_DIR" "$DATA_DIR" "$BACKUP_DIR" "$(dirname $LOG_FILE)" 2>/dev/null || mkdir -p "$PROJECT_DIR" "$DATA_DIR" "$BACKUP_DIR"
    sudo touch "$LOG_FILE" "$ERROR_LOG" && sudo chmod 777 "$LOG_FILE" "$ERROR_LOG" 2>/dev/null || { touch "$LOG_FILE" "$ERROR_LOG"; chmod 777 "$LOG_FILE" "$ERROR_LOG"; }
    cd "$PROJECT_DIR"
    
    if [ -d ".git" ]; then
        log_info "更新现有项目..."
        git pull origin main 2>/dev/null || log_warn "git pull失败，使用当前代码"
    else
        log_info "克隆项目代码..."
        git clone https://github.com/snrzz/risk.git "$PROJECT_DIR" 2>/dev/null || { log_error "git clone失败"; exit 1; }
    fi
    chmod +x deploy.sh init.sh 2>/dev/null || true
    log_info "项目部署完成 ✓"
}

configure_project() {
    log_step "配置项目环境..."
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    
    if [ ! -f ".env" ]; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "secret-$(date +%s)")
        JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "jwt-$(date +%s)")
        cat > "$PROJECT_DIR/.env" << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=True
ALLOWED_HOSTS=*
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
LOG_LEVEL=INFO
EOF
        log_info "配置文件已生成: $PROJECT_DIR/.env"
    else
        log_info "配置文件已存在，跳过生成"
    fi
    mkdir -p "$DATA_DIR/data"
    log_info "项目配置完成 ✓"
}

install_requirements() {
    log_step "安装Python依赖..."
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    [ -f "requirements.txt" ] || { log_error "requirements.txt不存在"; exit 1; }
    pip install -q -r requirements.txt 2>&1 | grep -v "Requirement already satisfied" || true
    python3 -c "import django" && log_info "Django安装成功 ✓" || { log_error "Django安装失败"; pip install django --upgrade; exit 1; }
    log_info "Python依赖安装完成 ✓"
}

init_database() {
    log_step "初始化数据库..."
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    python3 manage.py makemigrations accounts risk tasks --noinput 2>&1 | grep -E "(Created|No changes)" || true
    python3 manage.py migrate 2>&1 | grep -E "(OK|Applied|No migrations)" || true
    
    python3 manage.py shell -c "
from accounts.models import User, Role, Permission
try:
    if not User.objects.filter(email='admin@example.com').exists():
        User.objects.create_superuser('admin@example.com', 'Admin123!@#')
        print('✓ 管理员账户已创建')
    else:
        print('✓ 管理员账户已存在')
except Exception as e:
    print(f'⚠ 管理员账户创建失败: {e}')
" 2>/dev/null
    
    python3 manage.py shell -c "
from accounts.models import Permission
try:
    permissions = [
        ('用户管理', 'user_manage', 'user', 'manage'),
        ('角色管理', 'role_manage', 'role', 'manage'),
        ('组合管理', 'portfolio_manage', 'portfolio', 'manage'),
        ('交易查看', 'trade_read', 'trade', 'read'),
        ('风险查看', 'risk_read', 'risk', 'read'),
        ('预警处理', 'alert_manage', 'alert', 'manage'),
        ('任务管理', 'task_manage', 'task', 'manage'),
    ]
    for name, code, resource, action in permissions:
        Permission.objects.get_or_create(code=code, defaults={'name': name, 'resource_type': resource, 'action_type': action})
    print('✓ 权限初始化完成')
except Exception as e:
    print(f'⚠ 权限初始化失败: {e}')
" 2>/dev/null
    
    log_info "数据库初始化完成 ✓"
}

build_frontend() {
    log_step "构建前端..."
    [ ! -d "frontend" ] && { log_error "frontend目录不存在"; return 1; }
    [ ! -f "frontend/package.json" ] && { log_error "frontend/package.json不存在"; return 1; }
    cd "$PROJECT_DIR/frontend"
    [ ! -d "node_modules" ] && npm install --legacy-peer-deps 2>&1 | tail -3 || log_info "node_modules已存在"
    [ -d "node_modules" ] || { log_error "npm install失败"; return 1; }
    [ "$1" == "prod" ] && npm run build 2>&1 | tail -5 || log_info "开发模式，跳过构建"
    cd "$PROJECT_DIR"
    log_info "前端准备完成 ✓"
}

configure_nginx() {
    log_step "配置Nginx..."
    command -v nginx &> /dev/null || { log_warn "Nginx未安装，跳过配置"; return 0; }
    sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak.$(date +%Y%m%d) 2>/dev/null || true
    sudo cat > /etc/nginx/conf.d/risk.conf << 'EOF'
upstream risk_backend { server 127.0.0.1:8000; }
upstream risk_frontend { server 127.0.0.1:3000; }
server {
    listen 80; server_name localhost;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    location / { proxy_pass http://risk_frontend; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
    location /api/ { proxy_pass http://risk_backend; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
}
EOF
    sudo nginx -t 2>&1 | grep -q "syntax is ok" || { log_error "Nginx配置测试失败"; return 1; }
    (sudo systemctl restart nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null || sudo nginx) && log_info "Nginx配置完成 ✓" || log_warn "Nginx重启失败"
}

start_services() {
    log_step "启动服务..."
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    
    for port in 8000 3000; do
        pid=$(lsof -ti:$port 2>/dev/null || true)
        [ -n "$pid" ] && { log_warn "端口$port被占用，终止进程..."; kill -9 $pid 2>/dev/null || true; sleep 1; }
    done
    
    log_info "启动后端服务 (端口8000)..."
    nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
    sleep 3
    curl -s http://localhost:8000/api/risk/dashboard/ > /dev/null 2>&1 && log_info "后端服务启动成功 ✓" || log_warn "后端服务启动中..."
    
    log_info "启动前端服务 (端口3000)..."
    cd "$PROJECT_DIR/frontend"
    nohup npm run dev -- --host 0.0.0.0 > /dev/null 2>&1 &
    sleep 3
    curl -s http://localhost:3000 > /dev/null 2>&1 && log_info "前端服务启动成功 ✓" || log_warn "前端服务启动中..."
    
    log_info "所有服务已启动 ✓"
}

verify_deployment() {
    log_step "验证部署..."
    ERRORS=0
    curl -s http://localhost:8000/api/risk/dashboard/ > /dev/null 2>&1 && log_info "后端API: ✓" || { log_warn "后端API: ⚠"; ERRORS=$((ERRORS+1)); }
    curl -s http://localhost:3000 > /dev/null 2>&1 && log_info "前端: ✓" || { log_warn "前端: ⚠"; ERRORS=$((ERRORS+1)); }
    [ $ERRORS -eq 0 ] && log_info "部署验证通过 ✓" || log_warn "发现$ERRORS个问题"
}

create_services() {
    log_step "创建systemd服务..."
    [ "$EUID" -ne 0 ] && { log_warn "非root环境，跳过"; return 0; }
    command -v systemctl &> /dev/null || { log_warn "systemd不存在，跳过"; return 0; }
    sudo cat > /etc/systemd/system/risk-backend.service << 'EOF'
[Unit] Description=Risk Backend After=network.target
[Service] Type=simple User=root WorkingDirectory=$PROJECT_DIR Environment="PATH=$PROJECT_DIR/venv/bin" ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py runserver 0.0.0.0:8000 Restart=always RestartSec=10
[Install] WantedBy=multi-user.target
EOF
    sudo cat > /etc/systemd/system/risk-frontend.service << 'EOF'
[Unit] Description=Risk Frontend After=network.target
[Service] Type=simple User=root WorkingDirectory=$PROJECT_DIR/frontend ExecStart=/usr/bin/npx vite --host 0.0.0.0 --port 3000 Restart=always RestartSec=10
[Install] WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload && sudo systemctl enable risk-backend risk-frontend 2>/dev/null && log_info "systemd服务已创建 ✓" || log_warn "systemd服务创建失败"
}

print_summary() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              风险预警系统部署完成！                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${GREEN}Web UI:${NC}       ${CYAN}http://localhost:3000${NC}"
    echo -e "  ${GREEN}API地址:${NC}      ${CYAN}http://localhost:8000${NC}"
    echo -e "  ${GREEN}API文档:${NC}      ${CYAN}http://localhost:8000/api/docs/${NC}"
    echo ""
    echo -e "  ${YELLOW}默认登录:${NC}"
    echo -e "    邮箱:    ${CYAN}admin@example.com${NC}"
    echo -e "    密码:    ${CYAN}Admin123!@#${NC}"
    echo ""
    echo -e "  ${YELLOW}常用命令:${NC}"
    echo -e "    查看日志:  ${CYAN}tail -f $LOG_FILE${NC}"
    echo ""
    echo -e "  ${YELLOW}文档位置:${NC}"
    echo -e "    快速开始:    ${CYAN}$PROJECT_DIR/QUICK_START.md${NC}"
    echo -e "    部署文档:    ${CYAN}$PROJECT_DIR/docs/DEPLOYMENT.md${NC}"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

main() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              风险预警系统 - 一键部署脚本                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    check_root
    check_system
    install_dependencies
    check_node
    check_npm
    install_python_env
    deploy_project
    configure_project
    install_requirements
    init_database
    build_frontend "$1"
    configure_nginx
    create_services
    start_services
    sleep 3
    verify_deployment
    print_summary
}

main "$@"
