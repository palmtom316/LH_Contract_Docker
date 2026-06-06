# Cloudflare Tunnel 外网访问配置指南

## 概述

本文档介绍如何使用 Cloudflare Tunnel 让外网通过域名访问内网的合同管理系统。

### 优势
- ✅ **免费**：Cloudflare Tunnel 完全免费
- ✅ **自动 HTTPS**：Cloudflare 自动提供 SSL/TLS 证书
- ✅ **无需公网IP**：适用于家庭/企业内网
- ✅ **无需开放端口**：更安全，无需配置路由器端口转发
- ✅ **DDoS 防护**：Cloudflare 提供基础防护
- ✅ **隐藏真实IP**：增加安全性

---

## 前置条件

1. 一个域名（任意注册商均可）
2. Cloudflare 账号（免费注册）
3. 运行合同管理系统的 Linux 服务器（PVE 虚拟机）

---

## 第一步：将域名 DNS 托管到 Cloudflare

### 1.1 注册 Cloudflare 账号

1. 访问 [https://www.cloudflare.com/](https://www.cloudflare.com/)
2. 点击 "Sign Up" 注册账号
3. 验证邮箱

### 1.2 添加域名到 Cloudflare

1. 登录 Cloudflare Dashboard
2. 点击 "Add a site"
3. 输入您的域名（例如 `example.com`）
4. 选择 **Free** 计划，点击 Continue
5. Cloudflare 会自动扫描现有 DNS 记录

### 1.3 获取 Cloudflare DNS 服务器

Cloudflare 会提供两个 nameserver 地址，类似：
```
xxx.ns.cloudflare.com
yyy.ns.cloudflare.com
```

### 1.4 在域名注册商修改 DNS 服务器

**以 Starship 为例：**

1. 登录 Starship 域名管理控制台
2. 找到您的域名，进入管理页面
3. 找到 "DNS 设置" 或 "Nameserver" 设置
4. 将 DNS 服务器修改为 Cloudflare 提供的两个地址
5. 保存设置

> ⚠️ **注意**：DNS 更改可能需要 1-24 小时生效。可以使用 [https://dnschecker.org/](https://dnschecker.org/) 检查传播状态。

### 1.5 验证域名激活

1. 返回 Cloudflare Dashboard
2. 点击 "Check nameservers"
3. 如果显示 "Active"，表示域名已成功托管到 Cloudflare

---

## 第二步：安装 cloudflared

SSH 登录到运行合同管理系统的 PVE 虚拟机（VM）。

### 2.1 Debian/Ubuntu 系统

```bash
# 添加 Cloudflare 官方仓库
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null

# 添加软件源
echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# 更新并安装
sudo apt update
sudo apt install cloudflared -y

# 验证安装
cloudflared --version
```

### 2.2 其他安装方式

**直接下载二进制文件：**
```bash
# 64位 Linux
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
```

---

## 第三步：创建 Tunnel（推荐方式 - Dashboard）

### 3.1 进入 Zero Trust Dashboard

1. 访问 [https://one.dash.cloudflare.com/](https://one.dash.cloudflare.com/)
2. 首次使用需要创建团队名称（任意填写，如 `my-company`）
3. 选择 Free 计划

### 3.2 创建 Tunnel

1. 在左侧菜单找到 **Networks** → **Tunnels**
2. 点击 **Create a tunnel**
3. 选择 **Cloudflared** 作为连接类型
4. 命名隧道，例如：`lh-contract-tunnel`
5. 保存并进入下一步

### 3.3 在服务器上安装连接器

Cloudflare 会生成一个安装命令，类似：

```bash
sudo cloudflared service install eyJhIjoixxxxxxxxx...
```

在 VM 上执行这个命令。

### 3.4 配置公共主机名(Public Hostname)

在 Dashboard 中配置路由：

| 设置项 | 值 |
|-------|----|
| Subdomain | 留空（访问 example.com）或填 `www`（访问 www.example.com）|
| Domain | 选择您的域名 |
| Path | 留空 |
| Type | HTTP |
| URL | `localhost:80` |

点击 **Save tunnel** 完成配置。

---

## 第四步：验证服务状态

### 4.1 检查 cloudflared 服务

```bash
# 查看服务状态
sudo systemctl status cloudflared

# 查看日志
sudo journalctl -u cloudflared -f
```

### 4.2 检查隧道连接

在 Cloudflare Dashboard 的 Tunnels 页面，隧道状态应显示为 **Healthy**（绿色）。

### 4.3 访问测试

在浏览器中访问您的域名：
- `https://yourdomain.com`
- `https://www.yourdomain.com`（如果配置了）

---

## 第五步：高级配置（可选）

### 5.1 配置访问策略

如果需要限制访问（例如只允许特定用户），可以在 Zero Trust 中配置：

1. 进入 **Access** → **Applications**
2. 创建应用程序
3. 配置认证策略（邮箱验证、一次性密码等）

### 5.2 添加多个子域名

如果需要多个入口，在 Tunnel 配置中添加更多 Public Hostname：

| 用途 | 子域名 | 目标 |
|-----|-------|------|
| 主站 | `@` | `localhost:80` |
| WWW | `www` | `localhost:80` |
| API | `api` | `localhost:80` |

### 5.3 启用 Cloudflare 安全功能

在 Cloudflare Dashboard 中可以启用：
- **WAF（Web应用防火墙）**：防止常见攻击
- **Bot 管理**：阻止恶意机器人
- **Rate Limiting**：限制请求频率

---

## 故障排除

### 问题1：隧道状态显示 Degraded 或 Down

```bash
# 重启服务
sudo systemctl restart cloudflared

# 查看详细日志
sudo journalctl -u cloudflared -n 100
```

### 问题2：访问时显示 502 Bad Gateway

1. 确保 Docker 容器正在运行：
   ```bash
   docker ps
   ```
2. 确保 Nginx 在 80 端口正常监听：
   ```bash
   curl -v http://localhost:80
   ```

### 问题3：DNS 未生效

1. 使用 [dnschecker.org](https://dnschecker.org/) 检查 DNS 传播
2. 清除本地 DNS 缓存：
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Linux
   sudo systemd-resolve --flush-caches
   ```

### 问题4：证书错误

Cloudflare 自动管理证书，如果出现证书问题：
1. 确保 Cloudflare SSL/TLS 模式设置为 **Flexible** 或 **Full**
2. 等待证书生效（最多24小时）

---

## 常用命令参考

```bash
# 查看服务状态
sudo systemctl status cloudflared

# 启动服务
sudo systemctl start cloudflared

# 停止服务
sudo systemctl stop cloudflared

# 重启服务
sudo systemctl restart cloudflared

# 设置开机自启
sudo systemctl enable cloudflared

# 查看实时日志
sudo journalctl -u cloudflared -f

# 查看隧道信息
cloudflared tunnel info

# 列出所有隧道
cloudflared tunnel list
```

---

## 安全建议

1. **定期更新 cloudflared**：
   ```bash
   sudo apt update && sudo apt upgrade cloudflared
   ```

2. **启用 Cloudflare 的安全功能**：在 Dashboard 中开启 WAF、DDoS 防护等

3. **限制管理后台访问**：可以配置 Access Policy 只允许特定邮箱登录

4. **监控隧道状态**：定期检查 Dashboard 中的隧道健康状态

---

## 相关链接

- [Cloudflare Tunnel 官方文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
- [cloudflared GitHub](https://github.com/cloudflare/cloudflared)
