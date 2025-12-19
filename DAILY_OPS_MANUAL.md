# 蓝海合同管理系统 - 日常运维操作手册

本文档针对当前的 PVE + Docker 部署环境，为您提供最常用的操作指令。

## 1. 服务启停与管理

所有的 Docker 命令都需要在 `/opt/lh-contract` 目录下执行。

```bash
cd /opt/lh-contract
```

### ✅ 启动所有服务
```bash
sudo docker compose up -d
```
*这会自动启动数据库、Redis、后端、前端和 Nginx 网关。*

### ⏹️ 停止所有服务
```bash
sudo docker compose down
```
*这会优雅地停止并删除容器（数据保留）。*

### 🔄 重启个别服务
如果您修改了后端代码或配置：
```bash
sudo docker compose restart backend
```
如果是修改了 Nginx 配置：
```bash
sudo docker compose restart nginx
```

### 🔍 查看服务状态与日志
```bash
# 查看所有容器运行状态
sudo docker compose ps

# 查看后端实时日志 (按 Ctrl+C 退出)
sudo docker compose logs -f backend

# 查看数据库日志
sudo docker compose logs -f db
```

---

## 2. 关机流程 (推荐顺序)

为了保护数据库数据安全，建议按照以下顺序关机：

**第一步：停止 Docker 服务**
在 VM 终端执行：
```bash
cd /opt/lh-contract
sudo docker compose down
```

**第二步：关闭虚拟机 (VM)**
```bash
sudo poweroff
```
或者在 PVE 网页上点击该虚拟机，选择“关机”。

**第三步：关闭物理机 (PVE)**
在 PVE 网页左侧点击节点名称（如 `pve`），右上角选择“关机”。

---

## 3. 开机自启动设置

### Docker 容器自启
目前的配置文件 (`docker-compose.yml`) 中已经为所有服务配置了 `restart: always`。
**只要虚拟机开机且 Docker 服务启动，合同管理系统就会自动运行，无需人工干预。**

### PVE 虚拟机自启
若希望物理机通电后，虚拟机自动启动：
1. 登录 PVE 网页后台。
2. 选中您的虚拟机 (例如 ID 100)。
3. 点击中间菜单的 **“选项” (Options)**。
4. 双击 **“开机自启动” (Start at boot)**，勾选 Enabled。
5. (可选) 设置 **“启动/关机顺序”**：
   - Start/Shutdown order: 1
   - Startup delay: 0

---

## 4. 数据备份与恢复

虽然 PVE 提供了整机备份，但定期的应用级备份更加灵活。

### 💾 数据库备份 (全量)

您可以创建一个脚本 `backup_db.sh`：

```bash
#!/bin/bash
# 备份文件名包含时间戳
FILENAME="db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
# 备份目录 (建议挂载到外部或定期下载到本地)
BACKUP_DIR="/mnt/data/backups"
mkdir -p $BACKUP_DIR

# 执行备份命令
echo "正在备份数据库..."
sudo docker exec lh_contract_db pg_dump -U lh_admin lh_contract_db | gzip > "$BACKUP_DIR/$FILENAME"

echo "备份完成: $BACKUP_DIR/$FILENAME"
```

**恢复数据库：**
```bash
# ⚠️ 警告：这会覆盖当前数据
gunzip -c db_backup_xxxx.sql.gz | sudo docker exec -i lh_contract_db psql -U lh_admin lh_contract_db
```

### 📂 文件备份 (上传的合同)
您的所有上传文件都存储在扩容后的大硬盘：`/mnt/data/contract_uploads`。

**备份方法：**
使用 `tar` 打包：
```bash
sudo tar -czvf /mnt/data/backups/uploads_backup_$(date +%Y%m%d).tar.gz /mnt/data/contract_uploads
```

### 🖥️ PVE 整机备份 (最推荐)
这是最省心的灾备方案：
1. 在 PVE 网页选中虚拟机。
2. 点击 **“备份” (Backup)** -> **“立即备份” (Backup now)**。
3. 模式选择 **Snapshot** (快照模式，无需关机)。
4. 压缩选择 **ZSTD** (速度快)。
5. 点击备份。
*建议每周进行一次 PVE 整机备份。*

---

## 5. 常见问题 (FAQ)

**Q: 登录提示 "Network Error"？**
A: 请尝试强制刷新浏览器 (Ctrl+F5)。如果不行，检查 Nginx 状态：`sudo docker compose ps nginx`。

**Q: 上传文件提示空间不足？**
A: 检查大硬盘挂载情况：`df -h /mnt/data`。

**Q: 修改了代码没生效？**
A: 后端代码修改需要重启后端的容器：`sudo docker compose restart backend`。前端代码修改需要重新构建：`sudo docker compose build frontend && sudo docker compose up -d`。
