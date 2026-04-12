# 1.6.2 上线升级部署前最终审查报告

## 审查结论

结论：**当前分支 `1.6.2` 不建议直接上线**。

本次审查聚焦发布前最后一道门禁：生产可用性探针、部署配置一致性、既有发布清单与自动化验证是否真正覆盖运行风险。结论是存在 **2 个 P1 阻断项**、**2 个 P2 重要风险**。若按现状上线，最主要的问题不是“服务起不来”，而是 **依赖异常时仍会被判定为健康**，导致错误放行、延迟告警和错误恢复决策。

## 审查范围

- 后端启动与健康检查路径
- 生产部署配置与镜像内配置一致性
- 发布清单、升级 Runbook 与自动化测试覆盖
- 1.6.2 近期加固项与生产门禁对齐情况

## 主要发现

### P1-1 `/health/detailed` 在依赖异常时仍返回 HTTP 200，发布门禁与监控会被误判

**证据**

- [backend/app/routers/health.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/routers/health.py#L91) 计算了 `status_code`
- [backend/app/routers/health.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/routers/health.py#L103) 最终直接返回字典，没有把 `503` 写入响应
- [docs/release/deployment-checklist-hardening.md](/Users/palmtom/Projects/LH_Contract_Docker/docs/release/deployment-checklist-hardening.md#L58) 将 `curl -fsS http://localhost/health/detailed` 作为上线后必做检查

**影响**

- 只要应用进程还能响应，请求方就会拿到 `200 OK`，即使数据库、Redis 或 MinIO 已经处于 `unhealthy`
- `curl -f`、外部探针、变更工单验收都可能被错误放行
- 这会直接削弱 1.6.2 本轮“加固发布”的最后门禁价值

**复现摘要**

- 通过 `TestClient` 将数据库检查桩替换为 `unhealthy` 后，请求 `/health/detailed`
- 实际结果：`HTTP/1.1 200 OK`
- 响应体：`{"status":"unhealthy", ...}`

### P1-2 `/health/ready` 失败分支不会返回 503，而是以 200 返回错误形态的响应体

**证据**

- [backend/app/routers/health.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/routers/health.py#L110) 定义了 readiness probe
- [backend/app/routers/health.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/routers/health.py#L118) 采用 `return {"status": "not_ready"}, 503`
- 在 FastAPI 中这不会自动转成 HTTP 503，而是返回 `200 OK`，响应体近似 `[{...}, 503]`

**影响**

- readiness probe 语义失效，编排层或运维排障会认为服务“可接流量”
- 一旦数据库不可用，应用可能已经不具备服务能力，但探针仍返回成功状态码

**复现摘要**

- 通过 `TestClient` 将数据库检查桩替换为 `unhealthy` 后，请求 `/health/ready`
- 实际结果：`HTTP/1.1 200 OK`
- 响应体：`[{"status":"not_ready"},503]`

### P2-1 当前生产自动健康检查只校验 `/health`，没有真正校验数据库就绪状态

**证据**

- [docker-compose.production.yml](/Users/palmtom/Projects/LH_Contract_Docker/docker-compose.production.yml#L96) 后端容器健康检查调用 `http://localhost:8000/health`
- [backend/Dockerfile.production](/Users/palmtom/Projects/LH_Contract_Docker/backend/Dockerfile.production#L78) 镜像内 `HEALTHCHECK` 也调用 `/health`
- [nginx/nginx.conf](/Users/palmtom/Projects/LH_Contract_Docker/nginx/nginx.conf#L153) 对外 `/health` 代理到后端 `/health`
- [backend/app/main.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/main.py#L94) 的 `/health` 只是固定返回 `{"status":"healthy"}`

**影响**

- 自动化健康状态只证明“进程活着”，不能证明“服务可用”
- 即使数据库连接失败，容器和反向代理仍可能持续显示健康
- 与仓库中已经定义的 `/health/ready` 设计意图脱节，而且当前 `/health/ready` 本身又是失效的

### P2-2 前端镜像内 Nginx 配置仍暴露 `/uploads/` 静态目录，与生产安全基线发生漂移

**证据**

- [frontend/Dockerfile.production](/Users/palmtom/Projects/LH_Contract_Docker/frontend/Dockerfile.production#L43) 会把 [frontend/nginx.conf](/Users/palmtom/Projects/LH_Contract_Docker/frontend/nginx.conf#L47) 打进镜像
- [frontend/nginx.conf](/Users/palmtom/Projects/LH_Contract_Docker/frontend/nginx.conf#L47) 仍通过 `alias` 直接暴露 `/uploads/`
- [nginx/nginx.conf](/Users/palmtom/Projects/LH_Contract_Docker/nginx/nginx.conf#L148) 当前生产主配置已改为对 `/uploads/` 返回 `404`

**影响**

- 只要有人直接运行前端镜像、漏挂载根配置，或在其他环境复用该镜像，就会绕开当前附件访问加固
- 这是典型的镜像默认行为与生产安全策略不一致，容易在后续部署、灾备、临时环境中回归

### P2-3 发布契约测试只验证“路由存在”，没有验证健康检查的状态码语义

**证据**

- [backend/tests/test_release_contract.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/tests/test_release_contract.py#L14) 仅断言 `/health/detailed` 已挂载
- 全量搜索未发现对 `/health/detailed` 和 `/health/ready` 失败状态码的断言
- 本地执行 `PYTHONPATH=backend ./.venv/bin/pytest backend/tests/test_release_contract.py -q` 结果为 `4 passed`

**影响**

- 当前自动化能证明“有接口”，但不能证明“接口能作为发布门禁”
- 这正是两个 P1 问题可以带病通过的直接原因

## 结论分级

- **上线阻断项**
  - 修复 `/health/detailed` 非 200/503 语义错误
  - 修复 `/health/ready` 失败分支的 HTTP 状态码错误
- **上线前强烈建议一并完成**
  - 将容器与代理健康检查改为区分 `live` / `ready`
  - 清理前端镜像内 `/uploads/` 直接暴露配置
  - 增加健康检查失败分支的自动化回归测试

## 整改计划

### T0：上线前必须完成

1. 修复 [backend/app/routers/health.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/routers/health.py)
   - `/health/detailed` 使用 `JSONResponse(status_code=503, ...)` 或显式 `Response`
   - `/health/ready` 失败分支改为标准 `503`
2. 补测试
   - 新增 `/health/detailed` 在依赖 `unhealthy` 时返回 `503`
   - 新增 `/health/ready` 在数据库不可用时返回 `503`
3. 重新执行发布前验证
   - `PYTHONPATH=backend ./.venv/bin/pytest backend/tests/test_release_contract.py -q`
   - 新增的健康检查测试
   - `curl -fsS http://localhost/health`
   - `curl -fsS http://localhost/health/detailed`
   - 数据库断开或桩替换场景下验证 `/health/ready` 返回 `503`

### T1：本次上线窗口内建议完成

1. 调整健康检查职责
   - `/health/live` 仅做进程存活
   - `/health/ready` 作为编排层 readiness probe
   - `/health/detailed` 作为人工排障与发布验收接口
2. 修改以下配置使其对齐 `ready` 语义
   - [docker-compose.production.yml](/Users/palmtom/Projects/LH_Contract_Docker/docker-compose.production.yml)
   - [backend/Dockerfile.production](/Users/palmtom/Projects/LH_Contract_Docker/backend/Dockerfile.production)
   - [nginx/nginx.conf](/Users/palmtom/Projects/LH_Contract_Docker/nginx/nginx.conf)

### T2：上线后 1 个工作日内完成

1. 移除前端镜像默认 `uploads` 静态暴露
   - 修改 [frontend/nginx.conf](/Users/palmtom/Projects/LH_Contract_Docker/frontend/nginx.conf)
   - 明确仅允许通过后端鉴权链路访问附件
2. 清理版本元数据漂移
   - 当前 [backend/app/config.py](/Users/palmtom/Projects/LH_Contract_Docker/backend/app/config.py#L22) 为 `1.6.2`
   - 但 `.env` 与 `.env.production.example` 仍保留旧版本号，容易干扰本地验收与健康信息观测

## 审查说明

本次审查基于代码、部署配置、发布清单与最小化运行复现，不包含完整生产环境压测、真实证书链路、外部对象存储连通性和 Cloudflare/隧道侧实际探针配置复核。

## 建议的发布判定

- 当前状态：**不通过**
- 满足以下条件后可进入上线窗口
  - 两个 P1 已修复并通过自动化测试
  - 至少一个自动健康检查入口已切换到 readiness 语义
  - 附件访问策略在镜像默认行为与生产配置之间不再冲突
