# LH 合同管理系统 — 全栈深度代码审核报告

**审核日期**: 2026-07-25
**审核分支**: release/1.9.1
**审核范围**: 后端 ~13,000 行 Python（Models/Schemas/Routers/Services/Core/Migrations）+ 前端 ~15,000 行 JS/Vue + 基础设施（Docker/Nginx/Scripts）+ 测试 ~14,500 行
**审核方法**: 逐文件全文阅读 + 模式搜索验证（非采样扫描）

---

## 一、🔴 P0 — 安全漏洞（必须立即修复）

### S1. `token.json` 泄露管理员 JWT 令牌

**文件**: `token.json`（根目录，已提交 Git）
**内容**: admin 完整 access_token + refresh_token，过期到 2026 年

```json
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
"refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
"user":{"username":"admin","role":"ADMIN","is_superuser":true}}
```

**影响**: 任何克隆仓库者直接获得管理员权限。
**修复**: `git rm token.json` → 加入 `.gitignore` → 轮换 `SECRET_KEY` 使所有已签发令牌失效。

---

### S2. 系统重置端点执行 TRUNCATE 且无二次确认

**文件**: `backend/app/routers/system.py` ~line 640-660

```python
truncate_sql = f"TRUNCATE TABLE {', '.join(tables_to_truncate)} CASCADE"
await db.execute(text(truncate_sql))
await db.execute(text("DELETE FROM users WHERE is_superuser = false"))
```

该端点 `POST /system/reset` 仅要求 `is_superuser`，执行后会：
- TRUNCATE 所有业务表（合同、财务、审计日志）
- 删除所有非超级管理员用户
- 清空 uploads 目录

虽然 `tables_to_truncate` 来自硬编码列表（非注入），但该操作**极其危险且不可逆**：
- 无请求体确认（如 password 二次验证）
- 无审计日志记录（TRUNCATE 不触发审计）
- 无 dry-run 模式
- 删除用户后正在使用的 session 会残留

**修复**: 增加 `password` 字段二次验证 → 添加审计日志 → 仅在 `DEBUG=true` 时允许。

---

### S3. 飞书 Webhook Token 明文比较（时序攻击）

**文件**: `backend/app/routers/feishu.py` ~line 30

```python
if body.get("token") != FEISHU_WEBHOOK_VERIFICATION_TOKEN:
    raise HTTPException(status_code=403, detail="Invalid token")
```

Python `!=` 对字符串做逐字节比较，攻击者可通过响应时间差异逐字节猜出 token。

**修复**:
```python
import secrets
if not secrets.compare_digest(str(body.get("token", "")), FEISHU_WEBHOOK_VERIFICATION_TOKEN):
    raise HTTPException(status_code=403, detail="Invalid token")
```

---

### S4. 文件下载端点接受 URL 查询参数传 Token

**文件**: `backend/app/routers/common.py` — `get_file`

```python
@router.get("/files/{path:path}")
async def get_file(
    path: str,
    request: Request,
    token: Optional[str] = None,  # ← URL query param
    db: AsyncSession = Depends(get_db)
):
```

允许通过 `GET /api/v1/common/files/xxx?token=eyJhbGc...` 传递 JWT。Token 会出现在：
- Nginx access_log（`$request` 包含完整 URL）
- 浏览器历史记录
- 任何中间代理日志
- HTTP Referer 头

**修复**: 移除 `token` 查询参数，仅支持 Authorization 头。如需 PDF 预览（`<iframe>`/`<embed>`），改用短期一次性签名 URL。

---

### S5. 速率限制使用内存存储，多实例下失效

**文件**: `backend/app/core/rate_limit.py:77`

```python
limiter = Limiter(
    key_func=get_client_ip,
    # storage_uri="redis://redis:6379/1"  ← 注释掉了
)
```

`docker-compose.pve-prod.yml` 部署了 `backend` + `sync-worker` 两个容器。两者的限速计数器各自独立，实际限速上限翻倍。更严重的是，如果后端用 `uvicorn --workers N`，每个 worker 各自计数。

同时 `app/core/cache.py` 的 `CacheManager` **已连接 Redis** 且工作正常，说明 Redis 基础设施就绪，只是 rate limiter 没用。

**修复**: 取消注释 `storage_uri="redis://redis:6379/1"`。

---

## 二、🟠 P1 — 架构与逻辑缺陷

### A1. 双缓存系统互不相通，Dashboard 显示脏数据

项目中存在**两套独立的缓存**：

| 缓存 | 文件 | 后端 | 使用者 |
|---|---|---|---|
| `CacheService` | `app/services/cache.py` | 纯内存字典 | 所有 Service 层的 `_invalidate_dashboard_cache()` |
| `CacheManager` | `app/core/cache.py` | Redis + 内存 fallback | Dashboard Router 的 `@cache_manager.cached(ttl=300)` |

问题链：
1. 用户创建合同 → `ContractUpstreamService.create_contract()` → `cache.delete(dashboard_cache_key())` → **删除内存缓存**
2. Redis 中的 `dashboard:summary` 仍然存在 → Dashboard 接口返回**5分钟前的旧数据**
3. 5分钟后 Redis 缓存过期 → 才返回新数据

**修复**: 统一缓存层，Service 层使用 `cache_manager` 而非独立的 `cache` 实例。

---

### A2. 合同编号生成器存在竞态条件

**文件**: `backend/app/services/contract_code_generator.py`

```python
query = select(func.max(code_column)).where(code_column.like(f"{code_prefix}%"))
result = await self.db.execute(query)
max_code = result.scalar_one_or_none()
if max_code:
    seq = int(max_code.split("-")[-1]) + 1
else:
    seq = 1
return f"{code_prefix}{seq:03d}"
```

两个并发请求同时执行 `SELECT max(...)` → 都得到相同的 max_code → 生成相同的编号。虽然数据库的 `UNIQUE` 约束会阻止重复插入，但第二个请求会报 500 错误而非友好的重试。

**修复**: 使用 `SELECT ... FOR UPDATE` 或数据库序列（`CREATE SEQUENCE`），或在 catch 唯一约束冲突后重试。

---

### A3. 后台 Worker 在主进程和 sync-worker 中双重运行

**文件**: `backend/app/main.py:56` + `backend/run_sync.py`

`main.py` 的 `lifespan` 中启动 `_run_finance_import_worker`（while True + asyncio.sleep(2)），同时 `docker-compose.pve-prod.yml` 中有独立的 `sync-worker` 容器运行 `run_sync.py`。

两者都调用 `InvoiceImportService.claim_next_batch()`，虽然 `SKIP LOCKED` + `job_worker_token` 防止重复处理，但：
- 双重轮询浪费数据库连接
- 两个 worker 各持有连接池，增加数据库连接压力
- 逻辑冗余，维护负担

**修复**: 从 `main.py` 移除 `_run_finance_import_worker`，仅由 `sync-worker` 容器承载后台任务。

---

### A4. 前端 Token 存储在 localStorage（XSS 可窃取）

**文件**: `frontend/src/utils/authSession.js` + `frontend/src/utils/request.js`

```javascript
localStorage.setItem('token', accessToken)          // access token
localStorage.setItem('user_info', JSON.stringify(user))
localStorage.setItem('user_permissions', JSON.stringify(...))
sessionRefreshToken = refreshToken                   // 仅内存，refresh token 不入 localStorage ✓
```

Refresh token 已改进为仅存内存（移除了 `localStorage.setItem('refresh_token', ...)`），但 access token 仍在 localStorage。当前项目无 `v-html` 使用（已验证），XSS 面较小，但第三方库（Element Plus / Vant）若有 XSS 漏洞则可窃取 token。

**评估**: 对于内网部署的合同管理系统，风险可接受。如需加固，改用 httpOnly cookie + CSRF token。

---

### A5. `expense_service.approve_expense` 缺少权限校验

**文件**: `backend/app/services/expense_service.py` ~line 160

```python
async def approve_expense(self, expense_id: int, approved: bool, user: User) -> None:
    expense = await self.get_expense(expense_id)  # ← 无 current_user 传入
    # ← 没有检查 user.role 是否有审批权限
    expense.status = "已审核" if approved else "已驳回"
    expense.approved_by = user.id
```

调用该方法的 router `POST /expenses/{id}/approve` 也仅检查 `get_current_active_user`（登录即可），未检查具体权限。任何登录用户都可以审批/驳回费用。

**修复**: 在 router 中添加 `require_permission(Permission.EDIT_EXPENSES)` 或 `require_roles([UserRole.ADMIN, UserRole.FINANCE, UserRole.CONTRACT_MANAGER])`。

---

### A6. 审计日志归档后删除，但导出失败不可回退

**文件**: `backend/app/services/audit_archive_service.py` ~line 320

```python
async def archive_old_logs(self, days=90, export_format="json", delete_after_export=True):
    archive_file = await self.export_logs_to_json(before_date)
    if delete_after_export:
        deleted = await self.delete_logs_before_date(before_date)
```

如果 `export_logs_to_json` 在写入文件时遇到磁盘满但未抛异常（`json.dump` 成功但文件截断），删除操作仍会执行，导致审计日志永久丢失。

**修复**: 导出后验证文件完整性（行数/大小校验），验证通过后再删除。或先标记为归档，延迟删除。

---

### A7. `datetime.utcnow()` 已废弃 + 时区不一致

**影响范围**: 8+ 个文件

**关键问题位置**:
- `auth.py:72,124` — `user.last_login = datetime.utcnow()` (naive datetime)
- `auth.py` — JWT 过期时间 `datetime.utcnow() + expires_delta`
- `expense_service.py:190` — `expense.approved_at = datetime.utcnow()`
- `audit_archive_service.py` — `datetime.now()` (本地时间，非 UTC)

数据库列使用 `DateTime(timezone=True)`，写入 naive datetime 后 PostgreSQL 会解释为本地时间，与唯一使用 `datetime.now(timezone.utc)` 的 `invoice_import/service.py` 不一致。

**修复**: 全局替换为 `datetime.now(timezone.utc)`。

---

## 三、🟡 P2 — 代码质量与性能

### Q1. `contract_search.py` 的 ilike 未转义通配符

**文件**: `backend/app/routers/contract_search.py` — `_build_multi_value_ilike_condition`

```python
return column.ilike(f"%{normalized_values[0]}}%")
```

用户输入包含 `%` 或 `_` 时会被解释为 SQL 通配符。例如搜索 `%` 会匹配所有记录。

对比 `invoice_import/matching.py` 的 `_like_pattern` 正确做了转义：

```python
escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
```

**修复**: 在 `_build_multi_value_ilike_condition` 中使用相同的转义逻辑 + `escape="\\"`。

---

### Q2. Dashboard 趋势接口 N+1 查询模式

**文件**: `backend/app/routers/dashboard.py` — `get_period_trend`

```python
async def fill_map(stmt, target_map):
    res = await db.execute(stmt)
    for row in res.all():
        ...
# 调用4次，每次一个独立查询
await fill_map(stmt_downstream, downstream_map)
await fill_map(stmt_management, management_map)
await fill_map(stmt_non_contract, non_contract_map)
await fill_map(stmt_labor, labor_map)
```

4 个串行查询 + 收入查询 = 5 次数据库往返。可合并为 1 个 UNION ALL 查询。

---

### Q3. `feishu_service.py` 每次请求创建新 httpx.AsyncClient

```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, headers=headers, json=payload)
```

每次 API 调用创建/销毁 client，丢失连接池。应使用共享 client 实例。

---

### Q4. `users.py` 不防止 admin 删除自己

```python
@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
```

未检查 `user_id == current_user.id`，admin 可以删除自己，导致系统无管理员。

---

### Q5. Pydantic 响应模型金额类型不一致

- Schema 层（`contract_upstream.py` schemas）: `amount: Decimal` ✓
- `contract_search.py` 响应模型: `contract_amount: float = 0` ✗
- `dashboard.py` 响应: `"annual_upstream_amount": float(annual_upstream_amount)` ✗

JSON 序列化时 `float` 可能产生 `0.1 + 0.2 = 0.30000000000000004`。

---

### Q6. `db_check.py` 启动时自动加列掩盖迁移失败

```python
# V1.5 Required Columns - Auto-heal these on startup
REQUIRED_COLUMNS = { "contracts_upstream": [...] }
```

如果 Alembic 迁移失败但应用启动，`db_check` 会"修复"缺失的列。这掩盖了迁移问题，使数据库状态与迁移历史不一致。

---

### Q7. 裸 `except: pass` 静默吞噬异常

**统计**: 30+ 处

最关键的：
- `main.py:66` — shutdown 期间 `except: pass` 丢失清理错误
- `contract_upstream_service.py:287,298` — 财务计算中 `except: pass`
- `invoice_import/service.py:752` — 导入失败 `except Exception: pass`

**修复**: 至少 `logger.exception(...)` 记录栈回溯。

---

### Q8. Nginx CSP 允许 `unsafe-inline` + `unsafe-eval`

```
Content-Security-Policy "... script-src 'self' 'unsafe-inline' 'unsafe-eval'; ..."
```

Vue 3 + Vite 的生产构建不需要 `unsafe-eval`。`unsafe-inline` 可通过 nonce 方案替代。`Cross-Origin-Embedder-Policy: require-corp` 过于严格，会阻止加载第三方字体/图片。

---

### Q9. 前端 `router/index.js` 路由守卫中的权限检查基于 localStorage

```javascript
const permissions = JSON.parse(localStorage.getItem('user_permissions') || '[]')
```

用户可在浏览器控制台修改 localStorage 绕过前端路由守卫看到管理页面。虽然后端 API 会拦截，但 UX 不佳。建议权限来源改为从 store 响应式读取。

---

## 四、🔵 P3 — 次要问题

| # | 文件 | 问题 |
|---|---|---|
| P3.1 | `contracts_upstream.py:766` | 裸 `except:` 捕获删除关联记录时的异常 |
| P3.2 | `system.py:204` | 备份文件名使用 `datetime.now()` 无时区 |
| P3.3 | `invoice_imports.py:107` | 路由格式压缩到一行，可读性差 |
| P3.4 | 6 个 docker-compose 文件 | 应合并为 base + override |
| P3.5 | `expense_service.py:103,110` | `except: pass` 吞掉权限检查异常 |
| P3.6 | docker-compose pve | 镜像标签仍为 `1.9.0`，需更新为 `1.9.1` |
| P3.7 | Redis 容器 | 无持久化 + 无密码（内网可接受但应加注释说明） |
| P3.8 | MinIO health check | 使用 `curl`，镜像可能不含该工具 |

---

## 五、✅ 做得好的方面（逐行验证后确认）

| 领域 | 证据 |
|---|---|
| **XSS 防护** | 全项目零 `v-html` 使用（grep 验证），CSP 头设置 |
| **XXE 防护** | `parser.py` 使用 `defusedxml`，有 fallback 手动检测 DOCTYPE/ENTITY |
| **Zip Bomb 防护** | `archive.py` 检查文件数/解压大小/嵌套 zip，路径遍历检查 (`_assert_safe_member_name`) |
| **文件上传安全** | `file_validator.py` 使用 `python-magic` 做 MIME 签名校验 + 扩展名白名单 + 大小限制 |
| **文件下载防遍历** | `common.py` `_resolve_local_upload_path` 使用 `realpath` + `startswith` 检查 |
| **SQL 注入防护** | 全项目使用 SQLAlchemy ORM，`matching.py` 正确转义 ilike 通配符 |
| **Token 安全** | JWT access/refresh 分离、JTI 撤销、token rotation、refresh token 仅存内存 |
| **N+1 防护** | `contract_search.py` 30+ 处 `selectinload`，`lazy="raise"` 防意外懒加载 |
| **财务精度** | Model 层统一 `Numeric(15,2)`，posting 校验 `Decimal` 精确比较 |
| **发票入账防重** | `posting.py` 使用 `posting_version` 乐观锁 + `with_for_update()` 行锁 |
| **后台任务耐久** | `claim_next_batch` 使用 `SKIP LOCKED` + `job_worker_token` + 指数退避重试 |
| **文件授权** | `file_authorization.py` 23 条 FileAccessRule 覆盖所有业务模型的文件字段 |
| **日志脱敏** | `logging_config.py` 16 个正则模式过滤 password/token/secret/phone/idcard |
| **Nginx 安全** | 安全头完整（X-Frame/CSP/Referrer/Permissions）、`/uploads/` 返回 404、`/docs` 禁用 |
| **Vite 分包** | `manualChunks` 合理拆分 echarts/ep/vant/framework |
| **字典安全** | `dictionary_usage_service` 引用检查 + 停用而非删除 |
| **删除阻断** | `_get_delete_blockers` 检查关联数据后才允许删除合同 |
| **分摊平衡** | `Decimal` 精确比较 `abs(total - contract_amount) > Decimal("0.01")` |
| **测试覆盖** | 45 个测试文件覆盖 auth/permissions/finance/search/import/file/posting |
| **MinIO 备份路径安全** | `_safe_backup_object_path` 使用 `realpath` 防遍历 |

---

## 六、修复优先级总表

| 优先级 | 编号 | 问题 | 工作量 | 风险 |
|---|---|---|---|---|
| **P0** | S1 | `token.json` 泄露 | 0.5h | 数据泄露 |
| **P0** | S2 | 系统重置无确认 | 2h | 数据丢失 |
| **P0** | S3 | Webhook 时序攻击 | 0.5h | 权限绕过 |
| **P0** | S4 | URL 传 Token | 2h | Token 泄露 |
| **P0** | S5 | 速率限制内存存储 | 1h | 暴力破解 |
| **P1** | A1 | 双缓存不一致 | 4h | Dashboard 脏数据 |
| **P1** | A2 | 编号生成竞态 | 2h | 500 错误 |
| **P1** | A3 | Worker 双重运行 | 2h | 资源浪费 |
| **P1** | A4 | localStorage Token | 持续 | XSS 窃取 |
| **P1** | A5 | 费用审批无权限 | 1h | 权限绕过 |
| **P1** | A6 | 审计日志丢失 | 2h | 合规风险 |
| **P1** | A7 | datetime 废弃 | 3h | 时区错误 |
| **P2** | Q1 | ilike 未转义 | 1h | 搜索异常 |
| **P2** | Q2 | Dashboard N+1 | 2h | 性能 |
| **P2** | Q3 | httpx 连接泄漏 | 1h | 性能 |
| **P2** | Q4 | admin 自删 | 0.5h | 系统锁死 |
| **P2** | Q5 | float 金额 | 3h | 精度丢失 |
| **P2** | Q6 | db_check 掩盖迁移 | 2h | 数据不一致 |
| **P2** | Q7 | 裸 except: pass | 2h | 调试困难 |
| **P2** | Q8 | CSP unsafe-eval | 1h | XSS 加固 |
| **P2** | Q9 | localStorage 权限 | 2h | UX |
| **P3** | P3.1-P3.8 | 见上表 | 8h | 技术债 |

**P0 总工作量**: ~6h
**P1 总工作量**: ~14h
**P2 总工作量**: ~13.5h
**P3 总工作量**: ~8h
**总计**: ~41.5h

---

## 七、总结

项目整体工程质量较高——ORM 防注入、defusedxml 防XXE、zip bomb 防护、文件 MIME 校验、selectinload 防 N+1、posting 乐观锁防重、文件授权矩阵、日志脱敏等均已到位。全项目零 `v-html` 使用，SQL 注入面极小。

最紧急的 5 个 P0 问题中，`token.json` 泄露和系统重置端点应在部署前修复。架构层面，**双缓存不一致**是最隐蔽的问题——Service 清内存缓存、Router 读 Redis 缓存，导致 Dashboard 可能显示 5 分钟旧数据。**后台 worker 双重运行**虽然不会产生数据错误（SKIP LOCKED 保护），但浪费资源并增加连接池压力。

建议按 P0 → P1 → P2 的顺序，在后续 2-3 个迭代中逐步修复。
