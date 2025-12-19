#!/bin/bash
# 一键配置 LXC 容器使用 Clash 代理
# 使用方法：ssh root@192.168.72.101 'bash -s' < quick-setup-proxy.sh

PROXY_URL="http://192.168.72.41:7890"

echo "=========================================="
echo "配置 LXC 容器代理: ${PROXY_URL}"
echo "=========================================="

# 1. 配置系统环境变量
echo "1. 配置系统环境变量..."
cat >> /etc/environment << EOF
http_proxy="${PROXY_URL}"
https_proxy="${PROXY_URL}"
HTTP_PROXY="${PROXY_URL}"
HTTPS_PROXY="${PROXY_URL}"
no_proxy="localhost,127.0.0.1,192.168.72.0/24"
NO_PROXY="localhost,127.0.0.1,192.168.72.0/24"
EOF

# 2. 配置 APT 代理
echo "2. 配置 APT 代理..."
mkdir -p /etc/apt/apt.conf.d/
cat > /etc/apt/apt.conf.d/95proxies << EOF
Acquire::http::Proxy "${PROXY_URL}";
Acquire::https::Proxy "${PROXY_URL}";
EOF

# 3. 配置当前会话
echo "3. 配置当前会话..."
export http_proxy="${PROXY_URL}"
export https_proxy="${PROXY_URL}"
export HTTP_PROXY="${PROXY_URL}"
export HTTPS_PROXY="${PROXY_URL}"

# 4. 配置 Git 代理
echo "4. 配置 Git 代理..."
git config --global http.proxy "${PROXY_URL}" 2>/dev/null || true
git config --global https.proxy "${PROXY_URL}" 2>/dev/null || true

echo ""
echo "✅ 代理配置完成！"
echo ""
echo "当前代理设置："
echo "  HTTP_PROXY:  ${PROXY_URL}"
echo "  HTTPS_PROXY: ${PROXY_URL}"
echo ""
echo "测试代理连接："

# 测试代理
if command -v curl &> /dev/null; then
    if curl -s --connect-timeout 5 -I https://www.google.com > /dev/null 2>&1; then
        echo "  ✅ 可以访问 Google"
    else
        echo "  ❌ 无法访问 Google（请检查 Clash 是否运行）"
    fi
else
    echo "  ⚠️  curl 未安装，跳过测试"
fi

echo ""
echo "注意：新的 SSH 会话需要执行以下命令使代理生效："
echo "  source /etc/environment"
echo ""
