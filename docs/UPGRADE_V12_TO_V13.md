# LH 合同管理系统 V1.2 → V1.3 升级实战指南
> **最后更新日期**: 2025-12-30
> **适用环境**: Docker 部署 (Ubuntu/Linux VM)
> **验证状态**: ✅ 已验证成功

本文档记录了从 V1.2 升级到 V1.3 的完整流程、避坑指南及故障排除经验。请严格按照本指南操作。

---

## 🛑 核心原则 (避坑指南)

在开始之前，请务必阅读并遵守以下原则，这是多次失败总结出的血泪经验：

1.  **ROOT 权限是必须的**：
    *   不要试图用普通用户加 `sudo` 运行复杂脚本，文件重定向和目录创建会失败。
    *   **必须**先执行 `sudo -i` 切换到 root 用户。

2.  **Git 必须“绝对干净”**：
    *   如果有任何本地配置文件（如 `vite.config.js`）被修改过，`git checkout` 会失败，导致你以为升级了代码，实际还在旧版本。
    *   **必须**使用 `git reset --hard HEAD` 和 `git clean -fd` 强制清理。

3.  **认准容器名称**：
    *   V1.2 的数据库容器通常叫 `lh_contract_db`。
    *   V1.3 (生产配置) 的数据库容器叫 `lh_contract_db_prod`。
    *   备份时连接旧名字，恢复时连接新名字。

4.  **数据卷是最后的防线**：
    *   如果不小心删除了容器，只要没有加 `-v` 参数删除 Volume，数据就在。
    *   数据卷名称通常为 `lh-contract_postgres_data`。

---

## 📋 标准升级流程

### 第一步：身份切换与网络准备
打开终端，执行以下命令：

```bash
# 1. 切换到 root (必须!)
sudo -i

# 2. 清理 Git 代理 (防止连接 GitHub 失败/超时)
git config --global --unset http.proxy
git config --global --unset https.proxy
unset http_proxy https_proxy

# 3. 进入项目目录
cd /opt/lh-contract
```

### 第二步：数据备份 (至关重要)
我们将数据库导出为 SQL 文件，并备份上传文件。

```bash
# 1. 创建备份目录
BACKUP_DIR="/mnt/data/v1.3_upgrade_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/db_backup.sql"

# 2. 确认旧容器名称 (通常是 lh_contract_db)
OLD_DB_CONTAINER="lh_contract_db"

# 3. 导出数据库 (尝试不同的用户组合以防万一)
echo "💾 正在备份数据库..."
if docker exec $OLD_DB_CONTAINER pg_dump -U lh_admin lh_contract_db > "$BACKUP_FILE" 2>/dev/null; then
    echo "✅ 备份成功 (用户: lh_admin)"
elif docker exec $OLD_DB_CONTAINER pg_dump -U postgres lh_contract > "$BACKUP_FILE" 2>/dev/null; then
    echo "✅ 备份成功 (用户: postgres)"
elif docker exec $OLD_DB_CONTAINER pg_dump -U postgres lh_contract_db > "$BACKUP_FILE" 2>/dev/null; then
    echo "✅ 备份成功 (用户: postgres, 库: lh_contract_db)"
else
    echo "❌ 备份失败！无法导出数据库，请检查容器状态。"
    exit 1
fi

# 4. 备份上传文件
if [ -d "/mnt/data/contract_uploads" ]; then
    cp -r /mnt/data/contract_uploads "$BACKUP_DIR/uploads_copy"
    echo "✅ 上传文件已备份"
fi
```

### 第三步：代码升级 (强制切换)
这一步确保代码真正更新到 V1.3。

```bash
# 1. 强制清理本地修改 (防止 checkout 失败)
git reset --hard HEAD
git clean -fd

# 2. 拉取最新代码
git fetch --all
git checkout release/V1.3
git pull origin release/V1.3

# 3. 验证当前版本 (应显示 release/V1.3)
git status
```

### 第四步：部署新版本
使用生产环境配置 (`docker-compose.prod.yml`) 启动。

```bash
# 1. 清理旧容器 (防止命名冲突)
# 注意：这会删除旧容器，但数据卷保留
docker rm -f lh_contract_nginx lh_contract_frontend lh_contract_backend lh_contract_db lh_contract_redis 2>/dev/null

# 2. 启动新服务 (强制重新构建)
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

# 3. 检查状态
docker compose -f docker-compose.prod.yml ps
```

### 第五步：数据迁移/验证
V1.3 启动后，会自动挂载原有数据卷（如果有）。如果数据不一致，可使用备份恢复。

**检查清单：**
1.  **浏览器访问**：`http://192.168.72.101`
2.  **新功能检查**：确认是否有“查询机器人”功能（这是 V1.3 的标志）。
3.  **数据检查**：查看合同列表是否完整。

**如果需要恢复数据 (仅当数据缺失时执行)：**
```bash
# 导入此前备份的 SQL
cat "$BACKUP_FILE" | docker exec -i lh_contract_db_prod psql -U lh_admin -d lh_contract_db
```
*(注：可能会提示 constraint already exists，这是正常的)*

---

## ❓ 常见问题排查

### Q1: 升级后还是旧界面，没有新功能？
*   **原因**：Git 切换失败，本地仍是 V1.2 代码。
*   **检查**：运行 `git log -1`。如果显示 release/V1.2，说明你没切过去。
*   **解决**：执行 `git reset --hard HEAD` 然后再 `git checkout release/V1.3`。

### Q2: 提示 "No such container: lh_contract_db"？
*   **原因**：旧容器已经停止或被删除。
*   **解决**：运行 `docker ps -a` 查看。如果是 Exited，运行 `docker start ...`。如果没了，检查 `docker volume ls` 是否有数据卷。

### Q3: 数据库连接失败 / 密码错误？
*   **原因**：新版配置文件用了不同的密码或库名。
*   **解决**：检查 `docker-compose.prod.yml` 中的环境变量，确保与数据库实际用户匹配（通常是 `lh_admin` 或 `postgres`）。

---

## 🛠️ 常用维护命令

```bash
# 查看生产环境日志
docker compose -f docker-compose.prod.yml logs -f --tail 100

# 重启后端
docker compose -f docker-compose.prod.yml restart backend

# 进入数据库
docker exec -it lh_contract_db_prod psql -U lh_admin -d lh_contract_db
```

---

## 💾 附录：系统盘扩容优化 (迁移 Docker 数据)

如果发现系统盘 (`/`) 空间不足 (如使用率 >80%)，而数据盘 (`/mnt/data`) 空间充足，可以按照以下步骤将 Docker 的数据目录迁移到数据盘。

### 1. 检查磁盘状态
```bash
df -h
# 关注 "Mounted on" 为 "/" 的行。如果 Use% 很高，就需要迁移。
```

### 2. 停止 Docker 服务 (必须)
```bash
sudo systemctl stop docker
```

### 3. 下发迁移命令
这会将现有的 Docker 数据完整复制到新目录。
```bash
# 创建新目录
sudo mkdir -p /mnt/data/docker-data

# 复制数据 (注意斜杠)
sudo rsync -avP /var/lib/docker/ /mnt/data/docker-data/
```

### 4. 修改 Docker 配置文件
打开或创建配置文件：
```bash
sudo nano /etc/docker/daemon.json
```
**确保文件内容如下** (如果是新文件直接粘贴，如果已有内容请合并，**必须保证只有一个 `{}` 根对象**)：
```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://huecker.io",
    "https://dockerhub.timeweb.cloud",
    "https://noohub.ru"
  ],
  "data-root": "/mnt/data/docker-data"
}
```
*保存退出*: `Ctrl+O` -> Enter -> `Ctrl+X`

### 5. 重启并验证
```bash
# 启动 Docker
sudo systemctl start docker

# 验证根目录是否改变
docker info | grep "Docker Root Dir"
# 应显示: /mnt/data/docker-data

# 验证容器是否正常启动
docker ps
```

### 6. 清理旧数据 (释放空间)
确认一切正常后，删除旧数据释放系统盘空间。
```bash
sudo rm -rf /var/lib/docker
```
