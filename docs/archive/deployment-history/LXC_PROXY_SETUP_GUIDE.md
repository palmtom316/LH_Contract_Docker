# LXC 容器配置 Clash 代理指南

## 环境信息

- **笔记本 IP**: 192.168.72.41
- **Clash 端口**: 7890
- **LXC 容器 IP**: 192.168.72.101
- **代理地址**: http://192.168.72.41:7890

---

## 🚀 快速配置（推荐）

### 方法 1：使用自动配置脚本

1. **SSH 登录到 LXC 容器**
   ```bash
   ssh root@192.168.72.101
   ```

2. **下载并运行配置脚本**
   ```bash
   # 创建脚本
   cat > /tmp/setup-proxy.sh << 'EOF'
   #!/bin/bash
   PROXY_URL="http://192.168.72.41:7890"
   
   # 配置环境变量
   cat >> /etc/environment << EOL
   http_proxy="${PROXY_URL}"
   https_proxy="${PROXY_URL}"
   HTTP_PROXY="${PROXY_URL}"
   HTTPS_PROXY="${PROXY_URL}"
   no_proxy="localhost,127.0.0.1,192.168.72.0/24"
   NO_PROXY="localhost,127.0.0.1,192.168.72.0/24"
   EOL
   
   # 配置 APT 代理
   mkdir -p /etc/apt/apt.conf.d/
   cat > /etc/apt/apt.conf.d/95proxies << EOL
   Acquire::http::Proxy "${PROXY_URL}";
   Acquire::https::Proxy "${PROXY_URL}";
   EOL
   
   # 配置当前会话
   export http_proxy="${PROXY_URL}"
   export https_proxy="${PROXY_URL}"
   export HTTP_PROXY="${PROXY_URL}"
   export HTTPS_PROXY="${PROXY_URL}"
   
   echo "✅ 代理配置完成！"
   echo "代理地址: ${PROXY_URL}"
   EOF
   
   # 执行脚本
   chmod +x /tmp/setup-proxy.sh
   bash /tmp/setup-proxy.sh
   ```

3. **使配置生效**
   ```bash
   source /etc/environment
   ```

4. **测试代理**
   ```bash
   curl -I https://www.google.com
   ```

---

## 📝 方法 2：手动配置

### 步骤 1：配置系统环境变量

```bash
# SSH 登录到 LXC 容器
ssh root@192.168.72.101

# 编辑环境变量文件
nano /etc/environment

# 添加以下内容：
http_proxy="http://192.168.72.41:7890"
https_proxy="http://192.168.72.41:7890"
HTTP_PROXY="http://192.168.72.41:7890"
HTTPS_PROXY="http://192.168.72.41:7890"
no_proxy="localhost,127.0.0.1,192.168.72.0/24"
NO_PROXY="localhost,127.0.0.1,192.168.72.0/24"

# 保存并退出（Ctrl+O, Enter, Ctrl+X）
```

### 步骤 2：配置 APT 代理

```bash
# 创建 APT 代理配置
cat > /etc/apt/apt.conf.d/95proxies << EOF
Acquire::http::Proxy "http://192.168.72.41:7890";
Acquire::https::Proxy "http://192.168.72.41:7890";
EOF
```

### 步骤 3：配置当前会话

```bash
# 临时配置（立即生效）
export http_proxy="http://192.168.72.41:7890"
export https_proxy="http://192.168.72.41:7890"
export HTTP_PROXY="http://192.168.72.41:7890"
export HTTPS_PROXY="http://192.168.72.41:7890"
```

### 步骤 4：配置 Git 代理（可选）

```bash
git config --global http.proxy http://192.168.72.41:7890
git config --global https.proxy http://192.168.72.41:7890
```

### 步骤 5：配置 Docker 代理（如果需要）

```bash
# 创建 Docker 代理配置目录
mkdir -p /etc/systemd/system/docker.service.d

# 创建代理配置文件
cat > /etc/systemd/system/docker.service.d/http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=http://192.168.72.41:7890"
Environment="HTTPS_PROXY=http://192.168.72.41:7890"
Environment="NO_PROXY=localhost,127.0.0.1,192.168.72.0/24"
EOF

# 重新加载并重启 Docker
systemctl daemon-reload
systemctl restart docker
```

---

## 🧪 测试代理

### 1. 测试代理服务器连通性

```bash
# 安装 netcat（如果没有）
apt update && apt install -y netcat-openbsd

# 测试代理端口
nc -zv 192.168.72.41 7890
```

预期输出：
```
Connection to 192.168.72.41 7890 port [tcp/*] succeeded!
```

### 2. 测试 HTTP 代理

```bash
curl -I https://www.google.com
```

如果成功，会显示 Google 的 HTTP 响应头。

### 3. 测试 APT 更新

```bash
apt update
```

如果成功，会显示软件包列表更新。

### 4. 测试 Git 克隆

```bash
git clone https://github.com/torvalds/linux.git /tmp/test-clone
```

---

## ⚙️ 笔记本 Clash 配置检查

### 确保 Clash 允许局域网连接

1. **打开 Clash 配置文件**（通常是 `config.yaml`）

2. **检查以下设置**：
   ```yaml
   # 允许局域网连接
   allow-lan: true
   
   # 绑定地址（0.0.0.0 表示监听所有网卡）
   bind-address: '*'
   
   # HTTP 代理端口
   port: 7890
   
   # SOCKS5 代理端口
   socks-port: 7891
   ```

3. **重启 Clash** 使配置生效

### Windows 防火墙配置

如果连接失败，可能需要允许 Clash 通过防火墙：

1. 打开 **Windows Defender 防火墙**
2. 点击 **允许应用通过防火墙**
3. 找到 **Clash** 并勾选 **专用** 和 **公用**
4. 或者手动添加端口规则：
   ```powershell
   # 以管理员身份运行 PowerShell
   New-NetFirewallRule -DisplayName "Clash Proxy" -Direction Inbound -Protocol TCP -LocalPort 7890 -Action Allow
   ```

---

## 🔧 常用命令

### 查看当前代理配置

```bash
env | grep -i proxy
```

### 临时禁用代理

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

### 临时启用代理

```bash
export http_proxy="http://192.168.72.41:7890"
export https_proxy="http://192.168.72.41:7890"
```

### 测试特定 URL

```bash
# 使用代理访问
curl -x http://192.168.72.41:7890 https://www.google.com

# 不使用代理访问
curl --noproxy '*' https://www.baidu.com
```

---

## ❌ 删除代理配置

如果需要删除代理配置：

```bash
# 删除环境变量
sed -i '/proxy/d' /etc/environment

# 删除 APT 代理
rm /etc/apt/apt.conf.d/95proxies

# 删除 Git 代理
git config --global --unset http.proxy
git config --global --unset https.proxy

# 删除 Docker 代理
rm -rf /etc/systemd/system/docker.service.d/http-proxy.conf
systemctl daemon-reload
systemctl restart docker
```

---

## 🐛 故障排查

### 问题 1：无法连接到代理服务器

**检查项**：
1. Clash 是否正在运行
2. Clash 是否允许局域网连接（`allow-lan: true`）
3. 防火墙是否阻止了 7890 端口
4. 网络是否互通（`ping 192.168.72.41`）

**解决方法**：
```bash
# 测试网络连通性
ping 192.168.72.41

# 测试端口连通性
telnet 192.168.72.41 7890
# 或
nc -zv 192.168.72.41 7890
```

### 问题 2：代理配置不生效

**解决方法**：
```bash
# 重新加载环境变量
source /etc/environment

# 或者重新登录 SSH
exit
ssh root@192.168.72.101
```

### 问题 3：部分程序不走代理

**原因**：某些程序不读取环境变量

**解决方法**：
```bash
# 为特定程序指定代理
curl -x http://192.168.72.41:7890 https://example.com
wget -e use_proxy=yes -e http_proxy=192.168.72.41:7890 https://example.com
```

---

## 📊 代理配置总结

| 配置项 | 配置文件 | 作用范围 |
|--------|---------|---------|
| 系统环境变量 | `/etc/environment` | 所有用户和程序 |
| APT 代理 | `/etc/apt/apt.conf.d/95proxies` | APT 包管理器 |
| Git 代理 | `~/.gitconfig` | Git 命令 |
| Docker 代理 | `/etc/systemd/system/docker.service.d/` | Docker 守护进程 |
| 当前会话 | `export` 命令 | 当前终端会话 |

---

## ✅ 验证清单

- [ ] Clash 正在运行并允许局域网连接
- [ ] 防火墙允许 7890 端口
- [ ] LXC 容器可以 ping 通笔记本（192.168.72.41）
- [ ] 环境变量已配置（`/etc/environment`）
- [ ] APT 代理已配置
- [ ] 当前会话代理已生效（`env | grep proxy`）
- [ ] 可以访问 Google（`curl -I https://www.google.com`）
- [ ] APT 更新正常（`apt update`）

---

完成以上配置后，LXC 容器就可以通过笔记本的 Clash 代理翻墙了！🚀
