# VM 网络连通性测试脚本
# 用于测试虚拟机是否能访问 GitHub 和 Docker Hub

echo "=========================================="
echo "  VM 网络连通性测试"
echo "  测试时间: $(date)"
echo "=========================================="
echo ""

# 测试 1: 基本网络连通性
echo "🔍 测试 1: 基本网络连通性"
echo "-------------------------------------------"
ping -c 3 8.8.8.8 && echo "✅ 外网连通: 成功" || echo "❌ 外网连通: 失败"
echo ""

# 测试 2: DNS 解析
echo "🔍 测试 2: DNS 解析"
echo "-------------------------------------------"
nslookup github.com && echo "✅ DNS 解析 GitHub: 成功" || echo "❌ DNS 解析 GitHub: 失败"
nslookup hub.docker.com && echo "✅ DNS 解析 Docker Hub: 成功" || echo "❌ DNS 解析 Docker Hub: 失败"
echo ""

# 测试 3: GitHub 连接
echo "🔍 测试 3: GitHub 连接"
echo "-------------------------------------------"
curl -s --connect-timeout 10 https://github.com > /dev/null && echo "✅ GitHub HTTPS 连接: 成功" || echo "❌ GitHub HTTPS 连接: 失败"
curl -s --connect-timeout 10 https://api.github.com > /dev/null && echo "✅ GitHub API 连接: 成功" || echo "❌ GitHub API 连接: 失败"
echo ""

# 测试 4: Git 操作
echo "🔍 测试 4: Git 远程操作"
echo "-------------------------------------------"
if [ -d ".git" ]; then
    git ls-remote --exit-code origin > /dev/null 2>&1 && echo "✅ Git Remote 访问: 成功" || echo "❌ Git Remote 访问: 失败"
else
    echo "⚠️  当前目录不是 Git 仓库"
fi
echo ""

# 测试 5: Docker Hub 连接
echo "🔍 测试 5: Docker Hub 连接"
echo "-------------------------------------------"
curl -s --connect-timeout 10 https://registry-1.docker.io/v2/ > /dev/null && echo "✅ Docker Registry: 成功" || echo "❌ Docker Registry: 失败 (可能需要认证)"
docker pull hello-world > /dev/null 2>&1 && echo "✅ Docker Pull 测试: 成功" && docker rmi hello-world > /dev/null 2>&1 || echo "❌ Docker Pull 测试: 失败"
echo ""

# 测试 6: HTTPS 端口连通性
echo "🔍 测试 6: 端口连通性 (443)"
echo "-------------------------------------------"
timeout 5 bash -c "</dev/tcp/github.com/443" 2>/dev/null && echo "✅ GitHub:443 端口: 开放" || echo "❌ GitHub:443 端口: 阻塞"
timeout 5 bash -c "</dev/tcp/hub.docker.com/443" 2>/dev/null && echo "✅ Docker Hub:443 端口: 开放" || echo "❌ Docker Hub:443 端口: 阻塞"
echo ""

# 汇总
echo "=========================================="
echo "  测试完成"
echo "=========================================="
echo ""
echo "如果 GitHub 连接成功，可以使用 '方式A: GitHub 拉取' 升级"
echo "如果 GitHub 连接失败，请使用 '方式B: 局域网直接升级'"
echo ""
