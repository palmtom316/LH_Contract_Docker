# SSL 证书配置指南

## 为什么需要 SSL 证书？

- ✅ **数据加密**：保护用户数据传输安全
- ✅ **身份验证**：证明网站身份的真实性
- ✅ **SEO 优化**：搜索引擎优先展示 HTTPS 网站
- ✅ **浏览器信任**：避免浏览器显示"不安全"警告
- ✅ **合规要求**：满足数据保护法规要求

---

## 方案 1：使用 Let's Encrypt 免费证书（推荐）

Let's Encrypt 提供免费的 SSL 证书，有效期 90 天，支持自动续期。

### 步骤 1：安装 Certbot

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot

# CentOS/RHEL
sudo yum install certbot
```

### 步骤 2：获取证书（使用 Standalone 模式）

```bash
# 停止 Nginx（如果正在运行）
docker-compose -f docker-compose.prod.yml down

# 获取证书
sudo certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email

# 证书将保存在：
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### 步骤 3：复制证书到项目目录

```bash
# 创建 SSL 目录
mkdir -p nginx/ssl

# 复制证书
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/

# 设置权限
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

### 步骤 4：配置自动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# 添加定时任务（每天检查一次）
sudo crontab -e

# 添加以下行：
0 3 * * * certbot renew --quiet --post-hook "docker-compose -f /opt/lh_contract/docker-compose.prod.yml restart nginx"
```

---

## 方案 2：使用 Certbot Docker 容器（推荐用于 Docker 环境）

### 步骤 1：修改 docker-compose.prod.yml

```yaml
services:
  # ... 其他服务

  certbot:
    image: certbot/certbot
    container_name: lh_contract_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

  nginx:
    # ... 其他配置
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot/conf:/etc/nginx/ssl:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./uploads:/usr/share/nginx/html/uploads:ro
```

### 步骤 2：初始化证书

```bash
# 创建目录
mkdir -p certbot/conf certbot/www

# 首次获取证书（使用 webroot 模式）
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d yourdomain.com \
    -d www.yourdomain.com \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email

# 重启 Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 步骤 3：自动续期

Certbot 容器会每 12 小时检查一次证书，自动续期即将过期的证书。

---

## 方案 3：使用商业 SSL 证书

如果您购买了商业 SSL 证书（如 DigiCert, Comodo 等）：

### 步骤 1：获取证书文件

从证书提供商下载以下文件：
- `certificate.crt` - 证书文件
- `private.key` - 私钥文件
- `ca_bundle.crt` - 证书链文件（可选）

### 步骤 2：合并证书链

```bash
# 创建完整证书链
cat certificate.crt ca_bundle.crt > fullchain.pem

# 复制私钥
cp private.key privkey.pem
```

### 步骤 3：复制到项目目录

```bash
mkdir -p nginx/ssl
cp fullchain.pem nginx/ssl/
cp privkey.pem nginx/ssl/
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem
```

---

## 方案 4：自签名证书（仅用于开发/测试）

⚠️ **警告**：自签名证书不被浏览器信任，仅用于开发和测试环境！

### 生成自签名证书

```bash
# 创建 SSL 目录
mkdir -p nginx/ssl

# 生成私钥和证书（有效期 365 天）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=LH/OU=IT/CN=localhost"

# 设置权限
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem
```

---

## Nginx 配置更新

### 修改 nginx/nginx.conf

确保 SSL 证书路径正确：

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # Let's Encrypt 证书路径
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... 其他配置
}
```

---

## 验证 SSL 配置

### 1. 检查证书文件

```bash
# 检查证书有效期
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# 检查证书详细信息
openssl x509 -in nginx/ssl/fullchain.pem -noout -text

# 验证私钥和证书匹配
openssl x509 -noout -modulus -in nginx/ssl/fullchain.pem | openssl md5
openssl rsa -noout -modulus -in nginx/ssl/privkey.pem | openssl md5
# 两个 MD5 值应该相同
```

### 2. 测试 Nginx 配置

```bash
# 测试配置文件语法
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 重新加载配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 3. 在线 SSL 测试

访问以下网站测试 SSL 配置：
- [SSL Labs](https://www.ssllabs.com/ssltest/)
- [SSL Checker](https://www.sslshopper.com/ssl-checker.html)

目标评级：**A 或 A+**

---

## 常见问题

### Q1: 证书过期怎么办？

**Let's Encrypt：**
```bash
# 手动续期
sudo certbot renew

# 或者使用 Docker
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

**商业证书：**
- 联系证书提供商续费
- 下载新证书并替换旧证书

---

### Q2: 如何配置多个域名？

```bash
# Let's Encrypt 支持多个域名
sudo certbot certonly --standalone \
    -d domain1.com \
    -d www.domain1.com \
    -d domain2.com \
    -d www.domain2.com
```

---

### Q3: 证书路径权限问题

```bash
# 确保 Nginx 容器可以读取证书
sudo chown -R 101:101 nginx/ssl/  # Nginx 用户 UID
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

---

### Q4: 浏览器显示"不安全"

可能原因：
1. 证书过期
2. 证书域名不匹配
3. 证书链不完整
4. 使用自签名证书

解决方法：
```bash
# 检查证书有效期
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# 检查证书域名
openssl x509 -in nginx/ssl/fullchain.pem -noout -text | grep DNS
```

---

## 安全最佳实践

### 1. 使用强加密套件

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers off;
```

### 2. 启用 HSTS

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 3. 启用 OCSP Stapling

```nginx
ssl_stapling on;
ssl_stapling_verify on;
```

### 4. 定期更新证书

- Let's Encrypt：每 90 天自动续期
- 商业证书：提前 30 天续费

### 5. 监控证书过期

```bash
# 添加监控脚本
cat > /usr/local/bin/check-ssl-expiry.sh << 'EOF'
#!/bin/bash
DOMAIN="yourdomain.com"
DAYS_WARN=30

EXPIRY_DATE=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_WARN ]; then
    echo "WARNING: SSL certificate for $DOMAIN expires in $DAYS_LEFT days!"
fi
EOF

chmod +x /usr/local/bin/check-ssl-expiry.sh

# 添加到 crontab
echo "0 9 * * * /usr/local/bin/check-ssl-expiry.sh" | crontab -
```

---

## 部署检查清单

- [ ] SSL 证书已获取并复制到 `nginx/ssl/` 目录
- [ ] 证书文件权限正确（fullchain.pem: 644, privkey.pem: 600）
- [ ] Nginx 配置文件中的域名已修改为实际域名
- [ ] Nginx 配置文件语法测试通过（`nginx -t`）
- [ ] 已配置证书自动续期
- [ ] HTTPS 访问正常
- [ ] HTTP 自动重定向到 HTTPS
- [ ] SSL Labs 测试评级 A 或 A+
- [ ] 已启用 HSTS（可选）
- [ ] 已配置证书过期监控

---

## 总结

### 推荐方案

- **生产环境**：使用 Let's Encrypt（免费、自动续期）
- **企业环境**：使用商业证书（更长有效期、更好支持）
- **开发环境**：使用自签名证书（快速、简单）

### 下一步

1. 选择合适的 SSL 证书方案
2. 按照指南获取证书
3. 配置 Nginx
4. 测试 HTTPS 访问
5. 配置自动续期
6. 监控证书状态
