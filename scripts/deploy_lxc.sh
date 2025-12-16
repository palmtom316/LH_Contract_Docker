#!/bin/bash

################################################################################
# LH合同管理系统 - LXC自动部署脚本
# 版本: v1.1.0
# 用途: 在Debian/Ubuntu LXC容器中自动部署合同管理系统
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示标题
show_banner() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     LH合同管理系统 - LXC自动部署脚本 v1.1.0              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        log_info "检测到操作系统: $OS $VER"
    else
        log_error "无法检测操作系统"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统软件包..."
    apt update -qq
    apt upgrade -y -qq
    log_success "系统更新完成"
}

# 安装基础工具
install_basic_tools() {
    log_info "安装基础工具..."
    apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        net-tools \
        ca-certificates \
        gnupg \
        lsb-release \
        sudo \
        ufw \
        unzip \
        software-properties-common \
        apt-transport-https \
        > /dev/null 2>&1
    log_success "基础工具安装完成"
}

# 配置时区
configure_timezone() {
    log_info "配置时区为 Asia/Shanghai..."
    timedatectl set-timezone Asia/Shanghai
    log_success "时区配置完成: $(date)"
}

# 安装Docker
install_docker() {
    log_info "检查Docker安装状态..."
    
    if command -v docker &> /dev/null; then
        log_warning "Docker已安装，版本: $(docker --version)"
        return
    fi
    
    log_info "开始安装Docker..."
    
    # 卸载旧版本
    apt remove -y docker docker-engine docker.io containerd runc > /dev/null 2>&1 || true
    
    # 安装依赖
    apt update -qq
    
    # 设置Docker仓库
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$OS/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$OS \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    apt update -qq
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
    
    # 启动Docker
    systemctl start docker
    systemctl enable docker
    
    log_success "Docker安装完成: $(docker --version)"
    log_success "Docker Compose版本: $(docker compose version)"
}

# 配置Docker
configure_docker() {
    log_info "配置Docker..."
    
    mkdir -p /etc/docker
    
    cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
    
    systemctl daemon-reload
    systemctl restart docker
    
    log_success "Docker配置完成"
}

# 创建应用目录
create_app_directories() {
    log_info "创建应用目录..."
    
    APP_DIR="/opt/lh-contract"
    
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/data/postgres
    mkdir -p $APP_DIR/data/uploads
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/backups
    mkdir -p $APP_DIR/scripts
    
    log_success "应用目录创建完成: $APP_DIR"
}

# 克隆项目代码
clone_project() {
    log_info "克隆项目代码..."
    
    APP_DIR="/opt/lh-contract"
    
    if [ -d "$APP_DIR/.git" ]; then
        log_warning "项目已存在，拉取最新代码..."
        cd $APP_DIR
        git pull origin release/v1.1
    else
        log_info "从GitHub克隆项目..."
        cd /opt
        rm -rf lh-contract
        git clone -b release/v1.1 https://github.com/palmtom316/LH_Contract_Docker.git lh-contract
        cd lh-contract
        git checkout v1.1.0
    fi
    
    log_success "项目代码准备完成"
}

# 配置环境变量
configure_env() {
    log_info "配置环境变量..."
    
    APP_DIR="/opt/lh-contract"
    cd $APP_DIR
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
    
    # 获取容器IP
    CONTAINER_IP=$(hostname -I | awk '{print $1}')
    
    cat > .env << EOF
# 应用配置
APP_ENV=production
APP_NAME=LH合同管理系统
APP_VERSION=1.1.0

# 数据库配置
POSTGRES_DB=lh_contract
POSTGRES_USER=lhuser
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# 应用密钥
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET

# 后端配置
BACKEND_CORS_ORIGINS=["http://$CONTAINER_IP:3000","http://$CONTAINER_IP","http://localhost:3000"]
API_V1_PREFIX=/api/v1

# 前端配置
VITE_API_BASE_URL=http://$CONTAINER_IP:8000
VITE_APP_TITLE=LH合同管理系统

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379

# 文件上传配置
MAX_UPLOAD_SIZE=50MB
UPLOAD_DIR=/app/uploads

# 日志配置
LOG_LEVEL=INFO
EOF
    
    chmod 600 .env
    
    log_success "环境变量配置完成"
    log_info "数据库密码: $DB_PASSWORD"
}

# 部署应用
deploy_application() {
    log_info "部署应用..."
    
    APP_DIR="/opt/lh-contract"
    cd $APP_DIR
    
    # 检查docker-compose文件
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "找不到 docker-compose.prod.yml 文件"
        exit 1
    fi
    
    # 构建镜像
    log_info "构建Docker镜像（可能需要几分钟）..."
    docker compose -f docker-compose.prod.yml build
    
    # 启动服务
    log_info "启动服务..."
    docker compose -f docker-compose.prod.yml up -d
    
    log_success "应用部署完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 启用UFW
    ufw --force enable
    
    # 允许SSH
    ufw allow 22/tcp
    
    # 允许HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # 允许应用端口
    ufw allow 3000/tcp
    ufw allow 8000/tcp
    
    log_success "防火墙配置完成"
    ufw status
}

# 配置自动启动
configure_autostart() {
    log_info "配置服务自动启动..."
    
    cat > /etc/systemd/system/lh-contract.service << 'EOF'
[Unit]
Description=LH Contract Management System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/lh-contract
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable lh-contract.service
    
    log_success "自动启动配置完成"
}

# 创建备份脚本
create_backup_script() {
    log_info "创建备份脚本..."
    
    cat > /opt/lh-contract/scripts/backup_db.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/lh-contract/backups"
DB_CONTAINER="lh-contract-postgres"
DB_NAME="lh_contract"
DB_USER="lhuser"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/lh_contract_$(date +%Y%m%d_%H%M%S).sql.gz"

docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_FILE

find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup completed: $BACKUP_FILE" >> /opt/lh-contract/logs/backup.log
EOF
    
    chmod +x /opt/lh-contract/scripts/backup_db.sh
    
    # 添加定时任务
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/lh-contract/scripts/backup_db.sh") | crontab -
    
    log_success "备份脚本创建完成（每天凌晨2点自动备份）"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    sleep 10  # 等待服务启动
    
    cd /opt/lh-contract
    
    # 检查容器状态
    log_info "检查容器状态..."
    docker compose -f docker-compose.prod.yml ps
    
    # 检查后端健康
    CONTAINER_IP=$(hostname -I | awk '{print $1}')
    
    log_info "检查后端API健康状态..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "后端API运行正常"
    else
        log_warning "后端API健康检查失败，请检查日志"
    fi
    
    log_info "检查前端服务..."
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "前端服务运行正常"
    else
        log_warning "前端服务检查失败，请检查日志"
    fi
}

# 显示部署信息
show_deployment_info() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              部署完成！                                    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    CONTAINER_IP=$(hostname -I | awk '{print $1}')
    
    log_success "前端访问地址: http://$CONTAINER_IP:3000"
    log_success "后端API地址: http://$CONTAINER_IP:8000"
    log_success "API文档地址: http://$CONTAINER_IP:8000/docs"
    echo ""
    
    log_info "应用目录: /opt/lh-contract"
    log_info "数据目录: /opt/lh-contract/data"
    log_info "日志目录: /opt/lh-contract/logs"
    log_info "备份目录: /opt/lh-contract/backups"
    echo ""
    
    log_info "常用命令:"
    echo "  查看服务状态: cd /opt/lh-contract && docker compose -f docker-compose.prod.yml ps"
    echo "  查看日志: cd /opt/lh-contract && docker compose -f docker-compose.prod.yml logs -f"
    echo "  重启服务: cd /opt/lh-contract && docker compose -f docker-compose.prod.yml restart"
    echo "  停止服务: cd /opt/lh-contract && docker compose -f docker-compose.prod.yml down"
    echo "  启动服务: cd /opt/lh-contract && docker compose -f docker-compose.prod.yml up -d"
    echo ""
    
    log_warning "请妥善保存 .env 文件中的密码信息！"
    echo ""
}

# 主函数
main() {
    show_banner
    
    log_info "开始自动部署..."
    echo ""
    
    check_root
    detect_os
    update_system
    install_basic_tools
    configure_timezone
    install_docker
    configure_docker
    create_app_directories
    clone_project
    configure_env
    deploy_application
    configure_firewall
    configure_autostart
    create_backup_script
    health_check
    show_deployment_info
    
    log_success "部署完成！"
}

# 执行主函数
main "$@"
