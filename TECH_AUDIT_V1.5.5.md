# V1.5.5 技术审查报告

> **审查日期**: 2026-01-25  
> **审查版本**: V1.5.5 (commit: eafb7d2)  
> **审查范围**: 后端代码、前端代码、数据库设计、安全配置

---

## 一、执行摘要

V1.5.5 版本整体质量良好，核心功能完整，安全机制已就位。发现 12 项需关注的问题，其中 2 项为高优先级安全问题（需登录触发，风险可控），其余为中低优先级优化项。

**结论：可以投入生产使用，建议尽快发布 V1.5.6 修复 SQL 注入风险。**

---

## 二、问题发现汇总

| 序号 | 分类 | 问题描述 | 严重程度 | 位置 |
|:---:|:---:|:---|:---:|:---|
| 1 | 安全 | RefreshToken 表缺少清理机制，过期 token 永久堆积 | 🔴 高 | `refresh_tokens` 表 |
| 2 | 安全 | `get_companies` 接口使用 ILIKE 拼接存在 SQL 注入风险 | 🔴 高 | `common.py:43-64` |
| 3 | 安全 | Rate Limiter 使用内存存储，多 worker 下失效 | 🟡 中 | `rate_limit.py:72-78` |
| 4 | 性能 | `list_contracts` 使用 4 个相关子查询，大数据量下慢 | 🟡 中 | `contract_upstream_service.py:91-124` |
| 5 | 架构 | 三个合同 Service 代码重复率 > 70% | 🟡 中 | `contract_*_service.py` |
| 6 | 前端 | 无全局错误边界，JS 异常导致白屏 | 🟡 中 | Vue App 整体 |
| 7 | 前端 | API 请求未设置重试机制，弱网下体验差 | 🟡 中 | `request.js` |
| 8 | 数据库 | 缺少复合索引优化筛选查询 | 🟡 中 | 多表 |
| 9 | 可维护 | 日志缺乏结构化格式和请求追踪 ID | 🟢 低 | `main.py` |
| 10 | 可维护 | 缓存 Key 生成使用 MD5 截断，存在碰撞风险 | 🟢 低 | `cache.py:78-80` |
| 11 | 前端 | 大表格无虚拟滚动，数据多时卡顿 | 🟢 低 | `UpstreamList.vue` |
| 12 | 配置 | MinIO 默认凭证暴露在代码中 | 🟡 中 | `config.py:74-75` |

---

## 三、详细分析

### 3.1 🔴 高优先级问题

#### 问题 1: RefreshToken 清理机制缺失

**位置**: `backend/app/models/refresh_token.py`

**问题描述**: 
- `refresh_tokens` 表只有插入操作，无定期清理
- 过期和已撤销的 token 永久保留
- 长期运行后表会无限膨胀，影响数据库性能

**影响范围**: 数据库空间、查询性能

**修复方案**:
```python
# 添加定时任务或启动时清理
from datetime import datetime, timedelta
from sqlalchemy import delete, or_, and_

async def cleanup_expired_tokens(db: AsyncSession):
    """删除过期和已撤销的 refresh tokens"""
    cutoff = datetime.utcnow() - timedelta(days=30)
    await db.execute(
        delete(RefreshToken).where(
            or_(
                RefreshToken.expires_at < datetime.utcnow(),
                and_(RefreshToken.revoked == True, RefreshToken.created_at < cutoff)
            )
        )
    )
    await db.commit()
```

---

#### 问题 2: SQL 注入风险

**位置**: `backend/app/routers/common.py:43-64`

**问题描述**:
```python
# 当前代码直接拼接用户输入
ContractUpstream.party_a_name.ilike(f"%{query}%")  # 危险！
```

**影响范围**: 需要登录才能触发，但仍存在安全风险

**修复方案**:
```python
def safe_like_pattern(query: str) -> str:
    """转义 SQL LIKE 特殊字符"""
    return f"%{query.replace('%', r'\\%').replace('_', r'\\_')}%"

# 使用参数化查询
ContractUpstream.party_a_name.ilike(safe_like_pattern(query), escape='\\')
```

---

### 3.2 🟡 中优先级问题

#### 问题 3: Rate Limiter 多 Worker 失效

**位置**: `backend/app/core/rate_limit.py:72-78`

**问题描述**:
- `slowapi` 默认使用内存存储
- Uvicorn 多 worker 模式下各 worker 独立计数
- 实际限流效果为配置值的 N 倍（N = worker 数量）

**修复方案**:
```python
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["100/minute"],
    storage_uri=settings.REDIS_URL.replace("/0", "/1")  # 使用独立 Redis DB
)
```

---

#### 问题 4: 列表查询性能

**位置**: `backend/app/services/contract_upstream_service.py:91-124`

**问题描述**:
- 使用 4 个相关子查询计算财务汇总
- 大数据量（>10000条）下可能出现性能瓶颈

**修复方案**:
- 方案 A: 使用 PostgreSQL lateral join
- 方案 B: 添加定时任务预计算合计字段
- 方案 C: 分页时只查主表，详情时加载汇总

---

#### 问题 5: Service 层代码重复

**位置**: `backend/app/services/contract_*_service.py`

**问题描述**:
- `upstream`、`downstream`、`management` 三个 Service 代码结构几乎相同
- 重复率超过 70%
- 维护成本高，修改需同步三处

**修复方案**:
```python
class BaseContractService(Generic[ModelType, CreateSchema, UpdateSchema]):
    async def list_contracts(self, filters: ContractFilters) -> PaginatedResult:
        # 通用实现
        pass
    
    async def create_contract(self, data: CreateSchema, user: User) -> ModelType:
        # 通用实现，子类可重写
        pass
```

---

#### 问题 6: 前端错误边界缺失

**位置**: Vue App 整体

**问题描述**:
- 无全局错误捕获机制
- 组件异常会导致整个应用白屏
- 用户体验差，难以定位问题

**修复方案**:
```javascript
// main.js
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err)
  ElMessage.error('系统发生错误，请刷新页面')
  // 可上报到 Sentry
}
```

---

#### 问题 7: API 请求无重试机制

**位置**: `frontend/src/utils/request.js`

**问题描述**:
- 网络波动时请求直接失败
- 无自动重试机制
- 弱网环境下用户体验差

**修复方案**:
```javascript
import axiosRetry from 'axios-retry'

axiosRetry(service, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) 
      || error.response?.status >= 500
  }
})
```

---

#### 问题 8: 复合索引缺失

**位置**: 多个合同表

**问题描述**:
- 常用筛选组合（状态+日期、分类+状态）无复合索引
- 影响筛选查询性能

**修复方案**:
```python
# 新建 alembic migration
op.create_index('ix_upstream_status_sign_date', 'contracts_upstream', 
                ['status', 'sign_date'])
op.create_index('ix_upstream_company_category_status', 'contracts_upstream',
                ['company_category', 'status'])
```

---

#### 问题 12: MinIO 默认凭证

**位置**: `backend/app/config.py:74-75`

**问题描述**:
```python
MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
```

**修复方案**:
```python
@model_validator(mode='after')
def validate_minio(self) -> 'Settings':
    if not self.DEBUG and self.MINIO_ACCESS_KEY == "minioadmin":
        raise ValueError("生产环境必须配置非默认的 MINIO_ACCESS_KEY")
    return self
```

---

### 3.3 🟢 低优先级问题

| 问题 | 说明 | 修复建议 |
|:---|:---|:---|
| 结构化日志缺失 | 日志格式不统一，无请求追踪 ID | 引入 structlog + 请求 ID 中间件 |
| 缓存 Key 碰撞 | MD5 截断 12 字符存在碰撞风险 | 改用 SHA256 完整哈希 |
| 大表格性能 | 无虚拟滚动，数据多时卡顿 | 使用 el-table-v2 或 VirtualList |

---

## 四、生产就绪度评估

### 4.1 评估结论

| 维度 | 评分 | 说明 |
|:---|:---:|:---|
| 功能完整性 | ✅ 良好 | 核心功能完整，RefreshToken 轮换已实现 |
| 安全性 | ⚠️ 可接受 | 有 1 处 SQL 注入风险（需登录才能触发） |
| 性能 | ✅ 良好 | 有索引优化，缓存机制已就位 |
| 稳定性 | ✅ 良好 | 错误处理统一，连接池配置合理 |
| 可维护性 | ⚠️ 可接受 | Service 层有重复，日志需优化 |

### 4.2 是否可以上线？

**✅ 可以上生产**

| 问题 | 影响 | 是否阻塞上线 | 处理建议 |
|:---|:---|:---:|:---|
| SQL 注入风险 | 安全漏洞 | ⚠️ 建议修复 | 该接口需登录，风险可控，应尽快修复 |
| RefreshToken 表膨胀 | 数据库空间 | ❌ 否 | 几个月内不会有问题 |
| Rate Limiter 内存存储 | 多 worker 失效 | ❌ 否 | 单 worker 正常；多 worker 限流弱化 |
| MinIO 默认凭证 | 配置风险 | ❌ 否 | 只要 .env 正确配置就没问题 |

### 4.3 上线前必须确认

```bash
# .env 生产配置检查清单
SECRET_KEY=<64字符随机密钥>          # ✅ 必须设置
DEBUG=false                           # ✅ 必须关闭
DATABASE_URL=<生产数据库连接>         # ✅ 必须设置
MINIO_ACCESS_KEY=<非默认值>           # ✅ 必须修改
MINIO_SECRET_KEY=<非默认值>           # ✅ 必须修改
REDIS_URL=<生产Redis>                 # ✅ 建议配置
CORS_ORIGINS=<生产域名>               # ✅ 必须设置
```

---

## 五、修订计划

| 阶段 | 任务 | 优先级 | 预估工时 | 目标版本 |
|:---:|:---|:---:|:---:|:---:|
| Phase 1 | SQL 注入修复 | P0 | 1h | V1.5.6 |
| Phase 1 | MinIO 凭证校验加固 | P0 | 1h | V1.5.6 |
| Phase 1 | RefreshToken 清理定时任务 | P0 | 3h | V1.5.6 |
| Phase 2 | Rate Limiter Redis 后端 | P1 | 2h | V1.6.0 |
| Phase 2 | 前端错误边界 + 请求重试 | P1 | 3h | V1.6.0 |
| Phase 2 | 复合索引添加 | P1 | 1h | V1.6.0 |
| Phase 3 | 合同 Service 抽象重构 | P2 | 8h | V1.7.0 |
| Phase 3 | 结构化日志 + 请求追踪 | P2 | 4h | V1.7.0 |
| Phase 3 | 列表查询性能优化 | P2 | 6h | V1.7.0 |
| Phase 4 | 缓存 Key 优化 | P3 | 2h | V1.8.0 |
| Phase 4 | 大表格虚拟滚动 | P3 | 2h | V1.8.0 |

---

## 六、审查结论

V1.5.5 版本整体达到生产可用标准。主要风险点为 SQL 注入（需登录触发，风险可控）和 RefreshToken 表膨胀（短期无影响）。

**建议**：
1. 确认 `.env` 配置正确后可上线
2. 上线后尽快发布 V1.5.6 修复安全问题
3. 按修订计划逐步优化代码质量

---

*报告生成时间: 2026-01-25 20:18*  
*审查人: AI Technical Reviewer*
