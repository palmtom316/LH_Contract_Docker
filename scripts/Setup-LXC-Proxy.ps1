# PowerShell 脚本：配置 LXC 容器使用 Clash 代理
# 使用方法：在笔记本上运行此脚本

$LXC_IP = "192.168.72.101"
$PROXY_HOST = "192.168.72.41"
$PROXY_PORT = "7890"
$PROXY_URL = "http://${PROXY_HOST}:${PROXY_PORT}"

Write-Host "=========================================="
Write-Host "配置 LXC 容器代理"
Write-Host "LXC IP: $LXC_IP"
Write-Host "代理地址: $PROXY_URL"
Write-Host "=========================================="

# 配置脚本
$configScript = @"
PROXY_URL='$PROXY_URL'

echo '配置系统环境变量...'
cat >> /etc/environment << 'ENVEOF'
http_proxy="`$PROXY_URL"
https_proxy="`$PROXY_URL"
HTTP_PROXY="`$PROXY_URL"
HTTPS_PROXY="`$PROXY_URL"
no_proxy="localhost,127.0.0.1,192.168.72.0/24"
NO_PROXY="localhost,127.0.0.1,192.168.72.0/24"
ENVEOF

echo '配置 APT 代理...'
mkdir -p /etc/apt/apt.conf.d/
cat > /etc/apt/apt.conf.d/95proxies << 'APTEOF'
Acquire::http::Proxy "`$PROXY_URL";
Acquire::https::Proxy "`$PROXY_URL";
APTEOF

echo '配置当前会话...'
export http_proxy="`$PROXY_URL"
export https_proxy="`$PROXY_URL"
export HTTP_PROXY="`$PROXY_URL"
export HTTPS_PROXY="`$PROXY_URL"

echo ''
echo '✅ 代理配置完成！'
echo ''
echo '当前代理设置：'
echo "  HTTP_PROXY: `$PROXY_URL"
echo ''
"@

Write-Host ""
Write-Host "1. 连接到 LXC 容器并配置代理..."

# 执行配置
$result = $configScript | ssh root@$LXC_IP 'bash -s' 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 配置成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步："
    Write-Host "1. SSH 登录到 LXC: ssh root@$LXC_IP"
    Write-Host "2. 使配置生效: source /etc/environment"
    Write-Host "3. 测试代理: curl -I https://www.google.com"
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "❌ 配置失败！" -ForegroundColor Red
    Write-Host "错误信息: $result"
    Write-Host ""
    Write-Host "请检查："
    Write-Host "1. 是否可以 SSH 登录到 $LXC_IP"
    Write-Host "2. Clash 是否正在运行"
    Write-Host "3. Clash 是否允许局域网连接"
    Write-Host ""
}
