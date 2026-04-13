# PVE 生产升级交付记录与 3 天观察清单

## 交付摘要

- 交付日期: `2026-04-13`
- 目标环境: `palmtom@192.168.72.101`
- 应用目录: `/opt/lh-contract`
- 目标版本: `1.6.2`
- 生产代码提交: `43de2a3`
- 对外入口: `http://192.168.72.101/`
- 交付结论: 已完成升级、切换、启动验证与白屏修复，当前可正常对外提供服务

## 变更范围

### 后端与构建

- 修复 `backend/Dockerfile.production` 生产镜像构建失败问题，改为按 `requirements.txt` 从 wheel 目录安装依赖
- 保留现网数据库、Redis、MinIO 与上传目录，不在本次切换中做破坏性迁移

### PVE 生产编排

- 新增 `docker-compose.pve-prod.yml` 作为 PVE 专用生产编排
- 新增 `nginx/pve-prod.conf` 作为 PVE 对外入口配置
- 复用现有 Docker 网络 `lh-contract_lh_network`
- 解决 Nginx upstream 刷新问题，使用 `resolver 127.0.0.11` 与变量形式 upstream

### 前端稳定性

- 修复 `frontend/src/stores/user.js` 对历史脏 `localStorage` 的容错，避免非法 JSON 导致启动崩溃
- 新增 `frontend/src/stores/__tests__/user.spec.js`，覆盖损坏缓存和异常数据形态
- 调整 `frontend/vite.config.js`，将 Element Plus 相关依赖统一打入 `element-vendor`，消除 `element-form-vendor` 初始化时序错误
- 调整 `frontend/nginx.conf`，对 `index.html` 下发禁缓存头，避免浏览器继续使用旧入口文件

### 运维整理

- 调整 `nginx/default.conf`，统一 upstream 写法并修复 `/uploads/` 反向代理路径
- 移除多个 Compose 文件中的过时 `version` 字段，消除 Docker Compose `version` 警告

## 数据与回退点

- PVE snapshot: 已由现场提前完成
- 切换备份目录: `/opt/lh-contract-backups/prod-cutover-2026-04-13-172959`
- 已备份内容:
  - 数据库导出 `db.sql`
  - 上传文件归档 `uploads.tar`
  - `.env` 与 `.env.production`
  - `docker-compose.yml` 与 Nginx 配置
  - 容器 inspect、网络 inspect、容器列表
- 上传文件校验:
  - 文件数: `374`
  - 体积: `4.1G`

## 生产验证结果

### 服务状态

- `lh_contract_frontend`: `healthy`
- `lh_contract_backend`: 已通过健康检查
- `lh_contract_nginx`: `healthy`
- 入口页与 API 在切换后可正常访问

### 页面与业务验证

- 前端页面已恢复正常显示，不再出现蓝底白屏
- 用户登录后数据可正常加载
- 上传的 PDF 文件可正常访问与预览
- 首页当前引用的新静态资源为:
  - `index-CUdk2SXa.js`
  - `element-vendor-CeA5V8zt.js`

### 已确认的白屏根因

- 历史浏览器缓存中的异常 `localStorage` 数据可触发前端初始化失败
- Vite 手工拆分 Element Plus chunk 会触发 `Cannot access 'Gn' before initialization`
- 两项问题均已修复并已部署到生产环境

## 当前非阻塞项

- `favicon.svg 404` 不影响业务功能
- 浏览器扩展注入的 `webauthnInterceptor.js` 报错不属于系统自身故障
- 旧镜像、旧临时文件与额外备份暂不清理，建议观察期结束后统一处理

## 3 天观察清单

### Day 0 - 交付当日

- 确认 `docker compose -f docker-compose.pve-prod.yml --env-file .env.production ps` 全部关键容器为 `Up` 或 `healthy`
- 抽查登录、首页、合同列表、费用列表、报表页
- 抽查 PDF 上传、下载、预览
- 抽查 `/health` 与 `/health/ready`
- 记录是否出现 5xx、容器重启、明显性能抖动

### Day 1 - 交付后第 1 天

- 检查 `lh_contract_backend`、`lh_contract_frontend`、`lh_contract_nginx` 最近 24 小时日志
- 检查磁盘空间、内存占用、容器重启次数
- 抽查新增或编辑合同、查看财务与报表数据
- 抽查上传目录 `/mnt/data/contract_uploads` 是否持续增长且无异常权限问题

### Day 2 - 交付后第 2 天

- 再次确认页面未复发白屏
- 再次抽查 PDF 预览、下载、上传
- 检查是否存在用户反馈的权限、缓存、数据错乱问题
- 对比业务侧关键数据总量是否与切换前一致

### Day 3 - 交付后第 3 天

- 确认 72 小时内未出现持续性 5xx、反复重启或静态资源缓存异常
- 若运行稳定，可开始安排清理旧镜像与临时文件
- 若运行稳定，可评估删除旧开发态部署残留配置
- 若运行稳定，可决定是否归档或释放本次 snapshot 与切换备份

## 建议的观察期结束动作

- 导出一份最终稳定运行截图与容器状态记录
- 清理未使用镜像与临时补丁文件
- 保留至少一份数据库备份与一份上传文件备份
- 将本文件作为本次升级交付归档

## 回退说明

如观察期内发现严重问题，按以下顺序回退:

1. 先停止对外写入
2. 使用 PVE snapshot 回退整机状态，或恢复 `/opt/lh-contract-backups/prod-cutover-2026-04-13-172959` 中的配置与数据备份
3. 恢复数据库导出与上传文件归档
4. 恢复切换前的 Compose 与 Nginx 配置
5. 回退后重新验证首页、登录、数据与 PDF 访问
