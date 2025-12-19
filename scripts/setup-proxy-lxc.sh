#!/bin/bash
# LXC 容器代理配置脚本
# 通过笔记本 Clash 代理翻墙

# 代理服务器地址
PROXY_HOST="192.168.72.41"
PROXY_PORT="7890"
PROXY_URL="http://${PROXY_HOST}:${PROXY_PORT}"

echo "=========================================="
echo "配置 LXC 容器使用 Clash 代理"
echo "代理地址: ${PROXY_URL}"
echo "=========================================="

# 1. 配置环境变量（临时生效）
echo ""
echo "1. 配置临时环境变量..."
export http_proxy="${PROXY_URL}"
export https_proxy="${PROXY_URL}"
export HTTP_PROXY="${PROXY_URL}"
export HTTPS_PROXY="${PROXY_URL}"
export no_proxy="localhost,127.0.0.1,192.168.72.0/24"
export NO_PROXY="localhost,127.0.0.1,192.168.72.0/24"

echo "✅ 临时环境变量已设置"

# 2. 配置永久环境变量
echo ""
echo "2. 配置永久环境变量..."

# 备份原文件
if [ -f /etc/environment ]; then
    cp /etc/environment /etc/environment.bak.$(date +%Y%m%d_%H%M%S)
fi

# 删除旧的代理配置
sed -i '/http_proxy/d' /etc/environment 2>/dev/null
sed -i '/https_proxy/d' /etc/environment 2>/dev/null
sed -i '/HTTP_PROXY/d' /etc/environment 2>/dev/null
sed -i '/HTTPS_PROXY/d' /etc/environment 2>/dev/null
sed -i '/no_proxy/d' /etc/environment 2>/dev/null
sed -i '/NO_PROXY/d' /etc/environment 2>/dev/null

# 添加新的代理配置
cat >> /etc/environment << EOF
http_proxy="${PROXY_URL}"
https_proxy="${PROXY_URL}"
HTTP_PROXY="${PROXY_URL}"
HTTPS_PROXY="${PROXY_URL}"
no_proxy="localhost,127.0.0.1,192.168.72.0/24"
NO_PROXY="localhost,127.0.0.1,192.168.72.0/24"
EOF

echo "✅ 永久环境变量已配置（/etc/environment）"

# 3. 配置 APT 代理
echo ""
echo "3. 配置 APT 代理..."

mkdir -p /etc/apt/apt.conf.d/
cat > /etc/apt/apt.conf.d/95proxies << EOF
Acquire::http::Proxy "${PROXY_URL}";
Acquire::https::Proxy "${PROXY_URL}";
EOF

echo "✅ APT 代理已配置"

# 4. 配置 Git 代理
echo ""
echo "4. 配置 Git 代理..."

git config --global http.proxy "${PROXY_URL}"
git config --global https.proxy "${PROXY_URL}"

echo "✅ Git 代理已配置"

# 5. 配置 Docker 代理（如果安装了 Docker）
if command -v docker &> /dev/null; then
    echo ""
    echo "5. 配置 Docker 代理..."
    
    mkdir -p /etc/systemd/system/docker.service.d
    cat > /etc/systemd/system/docker.service.d/http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=${PROXY_URL}"
Environment="HTTPS_PROXY=${PROXY_URL}"
Environment="NO_PROXY=localhost,127.0.0.1,192.168.72.0/24"
EOF
    
    systemctl daemon-reload
    systemctl restart docker
    
    echo "✅ Docker 代理已配置"
else
    echo ""
    echo "5. Docker 未安装，跳过 Docker 代理配置"
fi

# 6. 配置 wget 代理
echo ""
echo "6. 配置 wget 代理..."

cat > ~/.wgetrc << EOF
http_proxy = ${PROXY_URL}
https_proxy = ${PROXY_URL}
use_proxy = on
EOF

echo "✅ wget 代理已配置"

# 7. 配置 curl 代理
echo ""
echo "7. 配置 curl 代理..."

cat > ~/.curlrc << EOF
proxy = "${PROXY_URL}"
EOF

echo "✅ curl 代理已配置"

# 8. 测试代理连接
echo ""
echo "=========================================="
echo "测试代理连接..."
echo "=========================================="

# 测试代理服务器连通性
echo ""
echo "1. 测试代理服务器连通性..."
if nc -zv ${PROXY_HOST} ${PROXY_PORT} 2>&1 | grep -q succeeded; then
    echo "✅ 代理服务器 ${PROXY_HOST}:${PROXY_PORT} 可访问"
else
    echo "❌ 代理服务器 ${PROXY_HOST}:${PROXY_PORT} 不可访问"
    echo "   请检查："
    echo "   - Clash 是否运行"
    echo "   - Clash 是否允许局域网连接（allow-lan: true）"
    echo "   - 防火墙是否阻止了 7890 端口"
fi

# 测试 Google 连接
echo ""
echo "2. 测试 Google 连接..."
if curl -s --connect-timeout 5 -x ${PROXY_URL} https://www.google.com > /dev/null 2>&1; then
    echo "✅ 可以通过代理访问 Google"
else
    echo "❌ 无法通过代理访问 Google"
fi

# 测试 GitHub 连接
echo ""
echo "3. 测试 GitHub 连接..."
if curl -s --connect-timeout 5 -x ${PROXY_URL} https://github.com > /dev/null 2>&1; then
    echo "✅ 可以通过代理访问 GitHub"
else
    echo "❌ 无法通过代理访问 GitHub"
fi

# 显示当前代理配置
echo ""
echo "=========================================="
echo "当前代理配置："
echo "=========================================="
echo "HTTP_PROXY:  ${HTTP_PROXY}"
echo "HTTPS_PROXY: ${HTTPS_PROXY}"
echo "NO_PROXY:    ${NO_PROXY}"

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "注意事项："
echo "1. 环境变量在当前会话立即生效"
echo "2. 新的 SSH 会话需要重新登录才能生效"
echo "3. 如需临时禁用代理，执行："
echo "   unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY"
echo ""
echo "4. 如需永久删除代理配置，执行："
echo "   sudo rm /etc/apt/apt.conf.d/95proxies"
echo "   sudo sed -i '/proxy/d' /etc/environment"
echo "   git config --global --unset http.proxy"
echo "   git config --global --unset https.proxy"
echo ""
