# Brand Sanitization Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 分批清理系统中残留的公司品牌与敏感示例信息，先消除运行时和模板对外暴露，再治理测试、脚本和文档中的品牌残留，同时避免误伤当前部署兼容性。

**Architecture:** 采用“先护栏、再分层治理、最后收口验收”的路径推进。第一层用自动化扫描与回归测试锁住运行时敏感词；第二层只修改用户可见默认值、系统回退值和导入模板；第三层再处理测试数据、脚本样例和文档残留；第四层将仓库代号、容器名、数据库名单列为兼容性决策项，不与前面批次混改。

**Tech Stack:** Vue 3, Pinia, Vite, FastAPI, Pytest, ripgrep, Git, Markdown

---

## 治理范围与分批策略

### P0: 立即治理

- 运行时界面默认品牌：
  - `frontend/src/views/Login.vue`
  - `frontend/src/views/Layout.vue`
  - `frontend/src/views/mobile/MobileLayout.vue`
  - `frontend/src/router/index.js`
  - `frontend/index.html`
  - `frontend/src/stores/system.js`
  - `frontend/src/views/system/SystemSettings.vue`
- 后端默认配置与模板示例：
  - `backend/app/routers/system.py`
  - `backend/app/routers/auth.py`
  - `backend/app/routers/contracts_upstream.py`

### P1: 第二批治理

- 测试数据与数据生成脚本：
  - `backend/tests/test_api_integration.py`
  - `backend/tests/test_contracts.py`
  - `backend/app/generate_downstream_test_data.py`
  - `backend/app/generate_management_test_data.py`
  - `backend/app/generate_upstream_test_data.py`
  - `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`

### P2: 第三批治理

- 主文档与用户/运维文档：
  - `README.md`
  - `REQUIREMENTS.md`
  - `DEPLOYMENT.md`
  - `OPERATIONS_MANUAL.md`
  - `docs/API_DOCUMENTATION.md`
  - `docs/USER_OPERATION_MANUAL.md`
  - `docs/USER_OPERATION_GUIDE_DETAILED.md`

### P3: 单独决策后再治理

- 兼容性敏感命名：
  - 仓库名 `LH_Contract_Docker`
  - Docker 容器名 `lh_contract_*`
  - 数据库名 `lh_contract_db`
  - 备份文件名 `lh_contract_db_*.sql`

## 文件边界与职责

- `backend/tests/test_frontend_default_content.py`
  - 已存在的前端默认内容护栏测试，扩展为覆盖更多运行时词汇。
- `backend/tests/test_brand_sanitization_runtime.py`
  - 新增运行时与后端默认值治理测试，覆盖前端回退文本、系统默认配置、导入模板示例。
- `frontend/src/views/Login.vue`
  - 登录页标题与副标题去品牌化。
- `frontend/src/views/Layout.vue`
  - PC 主布局的系统名回退值治理。
- `frontend/src/views/mobile/MobileLayout.vue`
  - 移动端主布局的页面标题回退值治理。
- `frontend/src/router/index.js`
  - 浏览器 `document.title` 拼接逻辑治理。
- `frontend/index.html`
  - 页面 `<title>` 与 `meta description` 默认文案治理。
- `frontend/src/stores/system.js`
  - 前端系统配置初始默认值去品牌化。
- `frontend/src/views/system/SystemSettings.vue`
  - 系统设置输入框 placeholder 去品牌化。
- `backend/app/routers/system.py`
  - 后端系统配置默认值与备份下载文件名治理边界确认。
- `backend/app/routers/auth.py`
  - 默认管理员邮箱样例去品牌化。
- `backend/app/routers/contracts_upstream.py`
  - 导入模板示例单位名去品牌化。
- `backend/app/generate_*.py`
  - 测试样例与生成脚本中的公司名去品牌化。
- `README.md` 及 `docs/**/*.md`
  - 面向外部文档中的品牌和样例公司名治理。
- `docs/reports/2026-04-08-brand-sanitization-inventory.md`
  - 新增扫描清单与决策记录，沉淀哪些命名已改、哪些命名因兼容性保留。

### Task 1: 建立治理护栏与基线清单

**Files:**
- Create: `backend/tests/test_brand_sanitization_runtime.py`
- Modify: `backend/tests/test_frontend_default_content.py`
- Create: `docs/reports/2026-04-08-brand-sanitization-inventory.md`

- [ ] **Step 1: 扩展前端敏感词护栏测试**

```python
from pathlib import Path


def test_frontend_runtime_source_has_no_brand_defaults():
    frontend_root = Path("frontend/src")
    blocked_terms = [
        "蓝海合同管理系统",
        "蓝海合同管理",
        "蓝海合同",
        "Lanhai Contract System",
        "admin@lanhai.com",
    ]

    matches = []
    for path in frontend_root.rglob("*"):
        if path.is_file() and path.suffix in {".vue", ".js", ".ts"}:
            content = path.read_text(encoding="utf-8")
            for term in blocked_terms:
                if term in content:
                    matches.append(f"{path}: {term}")

    assert not matches, "\n".join(matches)
```

- [ ] **Step 2: 新增后端默认值与模板示例测试**

```python
from pathlib import Path


def test_backend_defaults_and_templates_have_no_brand_terms():
    files = [
        Path("backend/app/routers/system.py"),
        Path("backend/app/routers/auth.py"),
        Path("backend/app/routers/contracts_upstream.py"),
    ]
    blocked_terms = [
        "蓝海合同管理系统",
        "admin@lanhai.com",
        "重庆蓝海电气",
    ]

    matches = []
    for path in files:
        content = path.read_text(encoding="utf-8")
        for term in blocked_terms:
            if term in content:
                matches.append(f"{path}: {term}")

    assert not matches, "\n".join(matches)
```

- [ ] **Step 3: 生成品牌残留基线清单**

```markdown
# 2026-04-08 品牌信息治理清单

## 立即治理
- frontend/src/views/Login.vue
- frontend/src/views/Layout.vue
- frontend/src/views/mobile/MobileLayout.vue
- frontend/src/router/index.js
- frontend/index.html
- frontend/src/stores/system.js
- frontend/src/views/system/SystemSettings.vue
- backend/app/routers/system.py
- backend/app/routers/auth.py
- backend/app/routers/contracts_upstream.py

## 延后决策
- docker-compose*.yml 中 `lh_contract_*`
- .env*.example 中 `lh_contract_db`
- 仓库名 `LH_Contract_Docker`
```

- [ ] **Step 4: 运行护栏测试并确认当前为红灯**

Run: `./.venv39/bin/pytest backend/tests/test_frontend_default_content.py backend/tests/test_brand_sanitization_runtime.py -q`
Expected: FAIL，并明确指出仍命中的 `蓝海` / `lanhai` 位置。

- [ ] **Step 5: 提交护栏基线**

```bash
git add backend/tests/test_frontend_default_content.py backend/tests/test_brand_sanitization_runtime.py docs/reports/2026-04-08-brand-sanitization-inventory.md
git commit -m "test: add brand sanitization guardrails"
```

### Task 2: 清理运行时品牌与后端默认值

**Files:**
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/index.html`
- Modify: `frontend/src/stores/system.js`
- Modify: `frontend/src/views/system/SystemSettings.vue`
- Modify: `backend/app/routers/system.py`
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/app/routers/contracts_upstream.py`
- Test: `backend/tests/test_frontend_default_content.py`
- Test: `backend/tests/test_brand_sanitization_runtime.py`

- [ ] **Step 1: 将前端回退文案改为中性系统名**

```vue
<h1 class="login-shell__title">合同管理系统</h1>
```

```js
const displayName = computed(() => systemStore.config.system_name || '合同管理系统')
const pageTitle = computed(() => route.meta.title || '合同管理')
document.title = to.meta.title ? `${to.meta.title} - 合同管理系统` : '合同管理系统'
```

- [ ] **Step 2: 将 HTML 和 Pinia 默认值改为中性占位**

```html
<meta name="description" content="合同、财务与项目管理平台">
<title>合同管理系统</title>
```

```js
system_name: '合同管理系统'
```

```vue
<el-input v-model="configForm.system_name" placeholder="例如：合同管理系统" />
```

- [ ] **Step 3: 清理后端默认值与模板示例**

```python
defaults = {
    "system_name": "合同管理系统",
}
```

```python
email: EmailStr = "admin@example.com"
```

```python
"乙方单位": ["示例单位A"],
```

- [ ] **Step 4: 运行目标测试与快速文本扫描**

Run: `./.venv39/bin/pytest backend/tests/test_frontend_default_content.py backend/tests/test_brand_sanitization_runtime.py -q`
Expected: PASS，显示 `2 passed`

Run: `rg -n "蓝海|重庆蓝海|lanhai|Lanhai" frontend/src frontend/index.html backend/app/routers/system.py backend/app/routers/auth.py backend/app/routers/contracts_upstream.py`
Expected: 无命中

- [ ] **Step 5: 提交运行时治理**

```bash
git add frontend/src/views/Login.vue frontend/src/views/Layout.vue frontend/src/views/mobile/MobileLayout.vue frontend/src/router/index.js frontend/index.html frontend/src/stores/system.js frontend/src/views/system/SystemSettings.vue backend/app/routers/system.py backend/app/routers/auth.py backend/app/routers/contracts_upstream.py
git commit -m "fix: remove runtime brand defaults"
```

### Task 3: 清理测试数据与生成脚本中的品牌样例

**Files:**
- Modify: `backend/tests/test_api_integration.py`
- Modify: `backend/tests/test_contracts.py`
- Modify: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
- Modify: `backend/app/generate_downstream_test_data.py`
- Modify: `backend/app/generate_management_test_data.py`
- Modify: `backend/app/generate_upstream_test_data.py`
- Test: `./.venv39/bin/pytest backend/tests/test_api_integration.py backend/tests/test_contracts.py -q`

- [ ] **Step 1: 将测试断言中的品牌公司改为中性公司名**

```python
party_a_name="示例建设集团"
party_b_name="示例电气工程有限公司"
```

```js
system_name: '合同管理系统'
```

- [ ] **Step 2: 将生成脚本默认样例改为通用公司名**

```python
PARTY_A_NAME = "示例建设工程有限公司"
PARTY_B_NAME = "示例机电工程有限公司"
project_categories = ["示例总公司", "示例子公司一", "示例子公司二"]
```

- [ ] **Step 3: 为测试与脚本新增一致性约束**

```python
assert "蓝海" not in PARTY_A_NAME
assert "蓝海" not in PARTY_B_NAME
```

- [ ] **Step 4: 运行相关测试与仓库扫描**

Run: `./.venv39/bin/pytest backend/tests/test_api_integration.py backend/tests/test_contracts.py -q`
Expected: PASS

Run: `rg -n "蓝海|重庆蓝海|lanhai|Lanhai" backend/tests backend/app/generate_* frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
Expected: 无命中，或仅命中治理文档/报告

- [ ] **Step 5: 提交样例数据治理**

```bash
git add backend/tests/test_api_integration.py backend/tests/test_contracts.py frontend/src/views/contracts/__tests__/UpstreamList.spec.js backend/app/generate_downstream_test_data.py backend/app/generate_management_test_data.py backend/app/generate_upstream_test_data.py
git commit -m "refactor: sanitize brand-specific sample data"
```

### Task 4: 清理主文档中的对外品牌与敏感样例

**Files:**
- Modify: `README.md`
- Modify: `REQUIREMENTS.md`
- Modify: `DEPLOYMENT.md`
- Modify: `OPERATIONS_MANUAL.md`
- Modify: `docs/API_DOCUMENTATION.md`
- Modify: `docs/USER_OPERATION_MANUAL.md`
- Modify: `docs/USER_OPERATION_GUIDE_DETAILED.md`
- Modify: `docs/reports/2026-04-08-brand-sanitization-inventory.md`

- [ ] **Step 1: 把面向读者的品牌名称统一改为产品中性名**

```markdown
# 合同管理系统 1.6
```

```markdown
本系统提供完整的 RESTful API，支持合同、财务与项目管理核心业务。
```

- [ ] **Step 2: 把样例公司名统一改为通用示例**

```markdown
甲方单位: 国网XX电力公司
乙方单位: 示例电气工程有限公司
```

- [ ] **Step 3: 保留兼容性敏感代号，但在清单中注明“暂不调整”**

```markdown
## 保留项
- `lh_contract_db`: 与现网数据库、备份脚本、升级文档兼容，暂不修改
- `lh_contract_backend`: 与现网容器名称兼容，暂不修改
- `LH_Contract_Docker`: 仓库名，需单独迁移评估
```

- [ ] **Step 4: 运行文档扫描**

Run: `rg -n "蓝海|重庆蓝海|lanhai|Lanhai" README.md REQUIREMENTS.md DEPLOYMENT.md OPERATIONS_MANUAL.md docs/API_DOCUMENTATION.md docs/USER_OPERATION_MANUAL.md docs/USER_OPERATION_GUIDE_DETAILED.md`
Expected: 无命中

- [ ] **Step 5: 提交文档治理**

```bash
git add README.md REQUIREMENTS.md DEPLOYMENT.md OPERATIONS_MANUAL.md docs/API_DOCUMENTATION.md docs/USER_OPERATION_MANUAL.md docs/USER_OPERATION_GUIDE_DETAILED.md docs/reports/2026-04-08-brand-sanitization-inventory.md
git commit -m "docs: sanitize external brand references"
```

### Task 5: 兼容性命名决策、验收与发布

**Files:**
- Modify: `docs/reports/2026-04-08-brand-sanitization-inventory.md`
- Optionally Modify: `.env.example`
- Optionally Modify: `.env.production.example`
- Optionally Modify: `docker-compose.yml`
- Optionally Modify: `docker-compose.production.yml`
- Optionally Modify: `docker-compose.prod.yml`
- Optionally Modify: `docker-compose.prod.balanced.yml`
- Optionally Modify: `docker-compose.prod.lowmem.yml`

- [ ] **Step 1: 对兼容性敏感命名做“不改 / 迁移改”的决策表**

```markdown
| 项目 | 当前值 | 动作 | 理由 |
| --- | --- | --- | --- |
| 仓库名 | LH_Contract_Docker | 暂不修改 | 涉及远端仓库迁移与地址变更 |
| 容器名 | lh_contract_* | 暂不修改 | 会影响运维脚本与现网部署 |
| 数据库名 | lh_contract_db | 暂不修改 | 会影响连接串、备份与升级脚本 |
```

- [ ] **Step 2: 跑全仓扫描并人工复核保留项**

Run: `rg -n --hidden --glob '!.git' --glob '!node_modules' --glob '!.venv39' --glob '!frontend/node_modules' --glob '!dist' "蓝海|重庆蓝海|蓝海建设|lanhai|Lanhai|LH_Contract|lh_contract|lan hai" .`
Expected: 仅剩已批准保留的仓库代号、容器名、数据库名、历史归档文档或治理测试文件

- [ ] **Step 3: 更新治理清单最终状态**

```markdown
## 验收结果
- 运行时品牌默认值: 已清理
- 导入模板品牌示例: 已清理
- 测试与脚本样例: 已清理
- 主文档品牌残留: 已清理
- 兼容性命名: 已登记保留
```

- [ ] **Step 4: 运行最终验证**

Run: `./.venv39/bin/pytest backend/tests/test_frontend_default_content.py backend/tests/test_brand_sanitization_runtime.py -q`
Expected: PASS

Run: `npm test --prefix frontend -- --runInBand`
Expected: PASS，或列出与品牌治理无关的既有失败项并在清单中注明

- [ ] **Step 5: 发布提交并推送**

```bash
git add docs/reports/2026-04-08-brand-sanitization-inventory.md .env.example .env.production.example docker-compose.yml docker-compose.production.yml docker-compose.prod.yml docker-compose.prod.balanced.yml docker-compose.prod.lowmem.yml
git commit -m "chore: document brand sanitization compatibility decisions"
git push origin 1.6
```

## 自检结论

- 已覆盖运行时前端文本、后端默认值、模板示例、测试样例、生成脚本、主文档和兼容性命名决策。
- 未把 `LH_Contract_Docker`、`lh_contract_*`、`lh_contract_db` 直接纳入立即修改范围，避免破坏部署与升级链路。
- 每个任务都给出了目标文件、示例代码、执行命令、预期输出和提交粒度，可直接按批执行。

## 执行建议

- 推荐先执行 Task 1 与 Task 2，尽快消除运行时对外暴露。
- Task 3 与 Task 4 可以串行执行，也可以拆给不同工程师分别处理。
- Task 5 必须在扫描结果确认后执行，避免误删现网兼容性标识。
