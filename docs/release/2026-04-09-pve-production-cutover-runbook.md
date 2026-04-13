# PVE 生产化切换运行手册

## 文档目的

本文档用于指导 `192.168.72.101` 这台 PVE 虚拟机在下班后切换到真正的生产部署形态。

目标不是单纯“升级代码”，而是把当前偏离生产规范的运行方式整理为可重复、可维护、可回滚的标准部署。

## 适用对象

- 运维操作人
- 负责晚间切换的值守人员
- 后续需要继续升级 `1.6.x` 的维护人员

## 主机与应用信息

- 主机: `palmtom@192.168.72.101`
- 应用目录: `/opt/lh-contract`
- 当前代码基线: `1.6.2`
- 当前对外入口: `http://192.168.72.101/`

## 一、当前现场状态

本手册基于 `2026-04-09` 的实际巡检结果编写，现场与仓库中的“生产部署参考”存在明显漂移。

### 1. 当前线上实际运行方式

- 前端容器使用的是开发模式:
  - 启动命令: `npm run dev -- --host 0.0.0.0 --port 3000`
  - 说明: 实际由 `vite dev` 提供服务，不是静态构建产物
- 后端容器使用的是开发模式:
  - 启动命令: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
  - 说明: 实际启用了 `--reload`
- Nginx、MinIO、sync-worker 已长期在线
- 数据库与 Redis 当前为容器内服务

### 2. 当前现场容器名

- `lh_contract_frontend`
- `lh_contract_backend`
- `lh_contract_db`
- `lh_contract_redis`
- `lh_contract_nginx`
- `lh_contract_minio`
- `lh_contract_sync_worker`

### 3. 当前现场网络

- Docker 网络: `lh-contract_lh_network`
- 当前线上依赖该网络中的服务名解析:
  - `backend`
  - `frontend`
  - `db`
  - `redis`

### 4. 当前现场与仓库文档/编排的不一致

- `docker-compose.prod.yml` 中的容器名是 `*_prod`，与线上现有容器名不一致
- `docker-compose.prod.yml` 的依赖关系与现场已有的 `nginx` / `minio` / `sync-worker` 不完全一致
- `docker-compose.production.yml` 也是另一套不同的生产编排，不应直接替代
- `docker-compose.prod.yml` 虽然把 `db` / `redis` / `backend` / `frontend` 命名成 `*_prod`，但 `nginx` 仍使用 `lh_contract_nginx`
- 因此如果现场旧 `lh_contract_nginx` 不先停掉并释放端口，就不能再直接 `up -d nginx`
- 旧文档中很多内容仍停留在历史版本，不能直接作为本机切换手册

结论:

- 本次晚间切换不能“直接执行现有 compose 文件”后赌它能自动接管现场
- 必须先按本手册整理备份、环境变量、目标编排和切换顺序
- 切换前必须先决定 `nginx` 是“纳入新编排重建”还是“保留旧容器仅替换后端/前端”，不能两种方式混用

## 二、目标状态

切换完成后，目标状态应满足以下条件。

### 1. 前端

- 使用 `frontend/Dockerfile.production`
- 容器内只运行 Nginx 静态站点
- 不再运行 `vite dev`

### 2. 后端

- 使用生产镜像
- 不再使用 `--reload`
- 明确加载 `.env.production`
- 通过 `http://backend:8000/health` 提供健康检查

### 3. 数据与依赖

- PostgreSQL 数据持久化
- Redis 数据持久化
- 上传目录继续使用宿主机路径或明确的持久化卷
- MinIO 继续保持现状，不在本次切换中重构
- `sync-worker` 如果依赖旧网络和旧服务名，切换时必须一起验证

### 4. 入口

- `nginx` 继续作为对外统一入口
- 对外健康检查:
  - `http://127.0.0.1/health`
  - `http://127.0.0.1:8000/health`

## 三、推荐切换策略

推荐采用“先固化目标编排，再做一次短时切换”的方式，不建议边停机边现场改文件。

### 推荐原则

- 先备份
- 先写死目标配置
- 先完成预演命令准备
- 晚间窗口只做:
  - 停旧容器
  - 启新容器
  - 验证
  - 必要时回滚

### 本次不建议纳入切换范围的事项

- 不改数据库结构
- 不迁移 MinIO 数据
- 不重构业务代码
- 不变更域名和 TLS 架构
- 不在切换窗口内“顺手修历史部署文档”

## 四、切换前必须完成的准备

以下工作建议在白天完成，并在晚间窗口前全部确认。

### 1. 固化目标生产编排

必须先整理出一份专用于这台机器的生产编排文件。建议命名为:

```bash
/opt/lh-contract/docker-compose.pve-prod.yml
```

要求:

- 只保留当前这台机器实际需要的服务
- 服务名统一为:
  - `db`
  - `redis`
  - `backend`
  - `frontend`
  - `nginx`
  - `minio`
  - `sync-worker`
- 若 `nginx` 也纳入该编排，切换步骤必须显式释放旧 `lh_contract_nginx` 的容器名和 `80/443` 端口
- 容器名与当前现场保持兼容，避免额外影响:
  - `lh_contract_db`
  - `lh_contract_redis`
  - `lh_contract_backend`
  - `lh_contract_frontend`
  - `lh_contract_nginx`
  - `lh_contract_minio`
  - `lh_contract_sync_worker`
- 网络统一使用:
  - `lh-contract_lh_network`

### 2. 固化目标环境变量

在切换前确认并备份以下文件:

```bash
/opt/lh-contract/.env
/opt/lh-contract/.env.production
```

要求:

- 生产切换统一以 `.env.production` 为准
- 密码、密钥、CORS、上传目录等值必须与现场真实可用值一致
- `DATABASE_URL` 必须指向 `db`
- `REDIS_URL` 必须指向 `redis`

### 3. 固化挂载目录

切换前确认以下目录的真实用途和归属:

- 上传目录
- 日志目录
- 备份目录
- Nginx 配置目录
- SSL 证书目录

至少确认以下路径是否仍在使用:

```bash
/opt/lh-contract/logs
/opt/lh-contract/backups
/mnt/data/contract_uploads
```

如果使用宿主机挂载上传目录，切换时必须保持挂载路径不变。

### 4. 备份

晚间切换前必须生成以下备份。

#### 数据库备份

```bash
sudo mkdir -p /opt/lh-contract-backups/production-cutover-$(date +%F)
sudo sh -c 'docker exec lh_contract_db pg_dump -U lh_admin lh_contract_db > /opt/lh-contract-backups/production-cutover-$(date +%F)/db.sql'
```

#### 环境文件备份

```bash
sudo cp /opt/lh-contract/.env /opt/lh-contract-backups/production-cutover-$(date +%F)/env.bak
sudo cp /opt/lh-contract/.env.production /opt/lh-contract-backups/production-cutover-$(date +%F)/env.production.bak
```

#### Nginx 配置备份

```bash
sudo cp -r /opt/lh-contract/nginx /opt/lh-contract-backups/production-cutover-$(date +%F)/nginx
```

#### 当前容器现场信息备份

```bash
sudo docker ps -a > /opt/lh-contract-backups/production-cutover-$(date +%F)/docker-ps.txt
sudo docker network inspect lh-contract_lh_network > /opt/lh-contract-backups/production-cutover-$(date +%F)/docker-network.json
```

### 5. 记录当前回滚点

在切换前记录:

- 当前 Git 提交号
- 当前正在运行的镜像 ID
- 当前容器配置

示例:

```bash
cd /opt/lh-contract
git rev-parse HEAD
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.ID}}'
```

## 五、建议的晚间切换步骤

以下步骤仅在“目标编排文件”和“目标环境变量文件”已经完成并人工复核后执行。

### 先决策: 本次是否重建 `nginx`

只能二选一，不能混用:

- 方案 A: `nginx` 一并纳入新编排
  - 需要在切换窗口内停止并移除旧 `lh_contract_nginx`
  - 新编排中的 `nginx` 接管 `80/443`
- 方案 B: 保留旧 `lh_contract_nginx`
  - 只切换 `backend` / `frontend`
  - 由旧 `nginx` 继续转发到新的应用容器

如果没有先做这个决策，后续命令极易出现容器名冲突或端口冲突。

### 第 1 步: 切换前最终确认

```bash
cd /opt/lh-contract
git status --short --branch
sudo docker ps
curl -fsS http://127.0.0.1/health
curl -fsS http://127.0.0.1:8000/health
```

验收标准:

- 当前站点仍然健康
- 没有未识别的现场临时改动

### 第 2 步: 构建生产镜像

示例命令:

```bash
cd /opt/lh-contract
sudo docker compose -f docker-compose.pve-prod.yml --env-file .env.production build backend frontend
```

验收标准:

- 前端镜像构建成功
- 后端镜像构建成功

### 第 3 步: 停掉将被替换的旧容器

注意:

- 先只停会被重建的应用层
- 若数据库与 Redis 本身已是目标生产形态，可不立即重建
- 若选择方案 A，必须一并停掉旧 `nginx`

示例:

```bash
sudo docker stop lh_contract_frontend lh_contract_backend
```

若本次选择方案 A，再执行:

```bash
sudo docker stop lh_contract_nginx
```

若新编排需要复用相同容器名，建议在确认备份已完成后释放旧容器名:

```bash
sudo docker rm lh_contract_frontend lh_contract_backend
```

若本次选择方案 A，再执行:

```bash
sudo docker rm lh_contract_nginx
```

### 第 4 步: 启动目标生产容器

方案 A 示例:

```bash
sudo docker compose -f docker-compose.pve-prod.yml --env-file .env.production up -d backend frontend nginx
```

方案 B 示例:

```bash
sudo docker compose -f docker-compose.pve-prod.yml --env-file .env.production up -d backend frontend
```

如果保留旧 `nginx` 容器，应在应用容器启动后人工检查并重载旧网关配置。

如果数据库和 Redis 也需要纳入统一编排，再执行:

```bash
sudo docker compose -f docker-compose.pve-prod.yml --env-file .env.production up -d db redis
```

### 第 5 步: 验证容器网络与服务名

```bash
sudo docker inspect lh_contract_backend --format '{{json .NetworkSettings.Networks}}'
sudo docker inspect lh_contract_db --format '{{json .NetworkSettings.Networks}}'
sudo docker inspect lh_contract_redis --format '{{json .NetworkSettings.Networks}}'
sudo docker exec lh_contract_backend getent hosts db
sudo docker exec lh_contract_backend getent hosts redis
```

验收标准:

- `backend` 能解析 `db`
- `backend` 能解析 `redis`
- 目标容器全部接入 `lh-contract_lh_network`
- 若保留旧 `nginx`，还要确认它仍能解析新的 `backend` / `frontend`

### 第 6 步: 验证健康状态

```bash
sudo docker ps
sudo docker logs --tail=100 lh_contract_backend
sudo docker logs --tail=100 lh_contract_frontend
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1/health
```

验收标准:

- 后端健康接口返回 `{"status":"healthy"}`
- Nginx 转发的 `/health` 返回 `{"status":"healthy"}`
- 前端不再显示 `vite` 开发服务器日志
- 后端不再显示 `--reload` 相关重载日志

### 第 7 步: 业务冒烟验证

至少人工验证以下页面和接口:

- 登录页
- 首页总览
- 经营分析页
- 合同列表页
- 历史附件下载/预览
- `GET /api/v1/system/options?category=expense_type`

## 六、回滚方案

如果切换后出现以下任一情况，应立即回滚:

- `http://127.0.0.1/health` 不通
- `http://127.0.0.1:8000/health` 不通
- 前端白屏
- 后端启动失败
- 登录失败
- 历史附件无法访问

### 回滚步骤

#### 1. 停掉新生产容器

如果本次选择方案 A:

```bash
sudo docker compose -f docker-compose.pve-prod.yml --env-file .env.production down
```

如果本次选择方案 B:

```bash
sudo docker compose -f docker-compose.pve-prod.yml --env-file .env.production stop backend frontend
```

#### 2. 按原现场方式启动旧容器

如果切换前保留了旧容器，可直接启动:

```bash
sudo docker start lh_contract_db lh_contract_redis lh_contract_backend lh_contract_frontend
```

如果回滚时旧 `nginx` 也曾被停掉，再执行:

```bash
sudo docker start lh_contract_nginx
```

如有网络别名丢失，补回:

```bash
sudo docker network connect --alias db lh-contract_lh_network lh_contract_db || true
sudo docker network connect --alias redis lh-contract_lh_network lh_contract_redis || true
sudo docker network connect --alias backend lh-contract_lh_network lh_contract_backend || true
sudo docker network connect --alias frontend lh-contract_lh_network lh_contract_frontend || true
```

#### 3. 回滚验证

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1/health
```

#### 4. 仅在确认数据损坏时恢复数据库

```bash
sudo sh -c 'cat /opt/lh-contract-backups/production-cutover-YYYY-MM-DD/db.sql | docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db'
```

原则:

- 先回滚应用
- 后回滚数据
- 不要在尚未确认数据损坏时贸然覆盖数据库

## 七、切换成功后的判定标准

满足以下全部条件，才可认定切换完成:

- 前端不再以 `vite dev` 运行
- 后端不再以 `uvicorn --reload` 运行
- `http://127.0.0.1/health` 正常
- `http://127.0.0.1:8000/health` 正常
- 不存在因旧 `lh_contract_nginx` 未释放而导致的新网关启动冲突
- 首页和经营分析页可正常打开
- 历史合同和历史费用记录可查询
- 历史附件可下载或预览
- `sync-worker` 未因服务名或网络变化失效

## 八、切换后建议补做事项

以下事项不要求在本次晚间切换窗口内完成，但应尽快纳入后续工作。

- 整理并统一生产编排文件，删除重复的 `docker-compose.prod.yml` / `docker-compose.production.yml` 分叉
- 统一容器命名策略，避免 `*_prod` 与线上真实容器名长期漂移
- 将 `.env.production` 的字段说明与真实生产需求彻底同步
- 为 `sync-worker` 补充明确的编排、依赖和健康检查
- 为 MinIO、uploads、数据库、Nginx 建立周期备份和恢复演练
- 写一份“标准升级 SOP”，把以后 `1.6.x` 升级流程固定下来

## 九、操作结论

这台 PVE 目前已经可以继续运行，但仍属于“能用，不算生产规范”的状态。

下班后切换时，必须按“先固化目标编排，再短窗切换”的思路执行，不能再直接拿仓库里的任一现成 compose 文件硬切。
