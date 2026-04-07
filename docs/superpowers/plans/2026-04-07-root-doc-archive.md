# Root Doc Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将根目录中的历史文档归档到 `docs/archive/` 下，同时保留当前 1.6 入口文档和运行配置在根目录。

**Architecture:** 采用“中等归档”方案，将历史版本/审计/阶段总结归入 `docs/archive/root-history/`，将历史部署/升级指南归入 `docs/archive/deployment-history/`。只修 `README.md` 当前入口链接，不批量重写历史文档内部引用。

**Tech Stack:** Git file moves, Markdown documentation, ripgrep verification

---

### Task 1: 建立归档目录并移动 root-history 文档

**Files:**
- Create: `docs/archive/root-history/`
- Modify: `RELEASE_NOTES_V1.1.md`
- Modify: `RELEASE_NOTES_V1.1.1.md`
- Modify: `RELEASE_NOTES_V1.2.md`
- Modify: `ARCH_IMPROVEMENT_PLAN.md`
- Modify: `REVISED_ARCH_PLAN.md`
- Modify: `OPTIMIZATION_OVERVIEW.md`
- Modify: `AUDIT_COMPLETION_REPORT.md`
- Modify: `CODE_AUDIT_REPORT.md`
- Modify: `CODE_REVIEW_REPORT.md`
- Modify: `PHASE1_IMPLEMENTATION_SUMMARY.md`
- Modify: `PHASE2_IMPLEMENTATION_SUMMARY.md`
- Modify: `PHASE3_IMPLEMENTATION_SUMMARY.md`
- Modify: `TECH_AUDIT_REPORT_2024_12_30.md`
- Modify: `TECH_AUDIT_REPORT_2026_01_15.md`
- Modify: `TECH_AUDIT_V1.5.5.md`
- Modify: `BETA2_DEBUGGING_SESSION.md`
- Modify: `ERROR_HANDLING_APPLIED.md`
- Modify: `ERROR_HANDLING_EXTENDED.md`
- Modify: `PDF_VIEW_FIX.md`

- [ ] **Step 1: 写删除前基线验证**

```bash
ls RELEASE_NOTES_V1.1.md RELEASE_NOTES_V1.1.1.md RELEASE_NOTES_V1.2.md ARCH_IMPROVEMENT_PLAN.md REVISED_ARCH_PLAN.md OPTIMIZATION_OVERVIEW.md AUDIT_COMPLETION_REPORT.md CODE_AUDIT_REPORT.md CODE_REVIEW_REPORT.md PHASE1_IMPLEMENTATION_SUMMARY.md PHASE2_IMPLEMENTATION_SUMMARY.md PHASE3_IMPLEMENTATION_SUMMARY.md TECH_AUDIT_REPORT_2024_12_30.md TECH_AUDIT_REPORT_2026_01_15.md TECH_AUDIT_V1.5.5.md BETA2_DEBUGGING_SESSION.md ERROR_HANDLING_APPLIED.md ERROR_HANDLING_EXTENDED.md PDF_VIEW_FIX.md
```

- [ ] **Step 2: 运行基线验证**

Run: 上述 `ls` 命令  
Expected: 所有待移动文件均存在于根目录

- [ ] **Step 3: 创建归档目录并移动文件**

```bash
mkdir -p docs/archive/root-history
mv RELEASE_NOTES_V1.1.md RELEASE_NOTES_V1.1.1.md RELEASE_NOTES_V1.2.md ARCH_IMPROVEMENT_PLAN.md REVISED_ARCH_PLAN.md OPTIMIZATION_OVERVIEW.md AUDIT_COMPLETION_REPORT.md CODE_AUDIT_REPORT.md CODE_REVIEW_REPORT.md PHASE1_IMPLEMENTATION_SUMMARY.md PHASE2_IMPLEMENTATION_SUMMARY.md PHASE3_IMPLEMENTATION_SUMMARY.md TECH_AUDIT_REPORT_2024_12_30.md TECH_AUDIT_REPORT_2026_01_15.md TECH_AUDIT_V1.5.5.md BETA2_DEBUGGING_SESSION.md ERROR_HANDLING_APPLIED.md ERROR_HANDLING_EXTENDED.md PDF_VIEW_FIX.md docs/archive/root-history/
```

- [ ] **Step 4: 验证 root-history 归档结果**

Run: `find docs/archive/root-history -maxdepth 1 -type f | sort`  
Expected: 上述 19 个文件均出现在 `docs/archive/root-history/`

- [ ] **Step 5: Commit**

```bash
git add docs/archive/root-history
git commit -m "chore: archive root history documents"
```

### Task 2: 建立 deployment-history 文档归档

**Files:**
- Create: `docs/archive/deployment-history/`
- Modify: `ALEMBIC_SETUP_GUIDE.md`
- Modify: `DAILY_OPS_MANUAL.md`
- Modify: `DEPLOYMENT_AND_MAINTENANCE_GUIDE.md`
- Modify: `DEPLOYMENT_CHECKLIST.md`
- Modify: `DEPLOYMENT_PVE_LXC.md`
- Modify: `GITHUB_UPLOAD_GUIDE.md`
- Modify: `LXC_PROXY_SETUP_GUIDE.md`
- Modify: `LXC_SSH_TROUBLESHOOTING.md`
- Modify: `OPS_STORAGE_EXPANSION_GUIDE.md`
- Modify: `PORT_CONFIGURATION_GUIDE.md`
- Modify: `PVE_LXC_DEPLOYMENT_GUIDE.md`
- Modify: `SSL_CERTIFICATE_GUIDE.md`
- Modify: `UPGRADE_GUIDE_V1.4.1_TO_V1.5.0.md`
- Modify: `UPGRADE_SAFETY_PROTOCOL.md`
- Modify: `UPGRADE_V1.1_TO_V1.2.md`
- Modify: `UPGRADE_V1.2.md`
- Modify: `UPGRADE_V1.3_TO_V1.3.2.md`
- Modify: `UPGRADE_V1.4.2.md`
- Modify: `V1.5.1_TO_V1.5.3_UPGRADE_GUIDE.md`
- Modify: `V1.5_COMPLETE_UPGRADE_GUIDE.md`
- Modify: `V1.5_PRODUCTION_UPGRADE_GUIDE.md`
- Modify: `1.5 版升级指令书.md`

- [ ] **Step 1: 写删除前基线验证**

```bash
ls ALEMBIC_SETUP_GUIDE.md DAILY_OPS_MANUAL.md DEPLOYMENT_AND_MAINTENANCE_GUIDE.md DEPLOYMENT_CHECKLIST.md DEPLOYMENT_PVE_LXC.md GITHUB_UPLOAD_GUIDE.md LXC_PROXY_SETUP_GUIDE.md LXC_SSH_TROUBLESHOOTING.md OPS_STORAGE_EXPANSION_GUIDE.md PORT_CONFIGURATION_GUIDE.md PVE_LXC_DEPLOYMENT_GUIDE.md SSL_CERTIFICATE_GUIDE.md UPGRADE_GUIDE_V1.4.1_TO_V1.5.0.md UPGRADE_SAFETY_PROTOCOL.md UPGRADE_V1.1_TO_V1.2.md UPGRADE_V1.2.md UPGRADE_V1.3_TO_V1.3.2.md UPGRADE_V1.4.2.md V1.5.1_TO_V1.5.3_UPGRADE_GUIDE.md V1.5_COMPLETE_UPGRADE_GUIDE.md V1.5_PRODUCTION_UPGRADE_GUIDE.md "1.5 版升级指令书.md"
```

- [ ] **Step 2: 运行基线验证**

Run: 上述 `ls` 命令  
Expected: 所有待移动文件均存在于根目录

- [ ] **Step 3: 创建归档目录并移动文件**

```bash
mkdir -p docs/archive/deployment-history
mv ALEMBIC_SETUP_GUIDE.md DAILY_OPS_MANUAL.md DEPLOYMENT_AND_MAINTENANCE_GUIDE.md DEPLOYMENT_CHECKLIST.md DEPLOYMENT_PVE_LXC.md GITHUB_UPLOAD_GUIDE.md LXC_PROXY_SETUP_GUIDE.md LXC_SSH_TROUBLESHOOTING.md OPS_STORAGE_EXPANSION_GUIDE.md PORT_CONFIGURATION_GUIDE.md PVE_LXC_DEPLOYMENT_GUIDE.md SSL_CERTIFICATE_GUIDE.md UPGRADE_GUIDE_V1.4.1_TO_V1.5.0.md UPGRADE_SAFETY_PROTOCOL.md UPGRADE_V1.1_TO_V1.2.md UPGRADE_V1.2.md UPGRADE_V1.3_TO_V1.3.2.md UPGRADE_V1.4.2.md V1.5.1_TO_V1.5.3_UPGRADE_GUIDE.md V1.5_COMPLETE_UPGRADE_GUIDE.md V1.5_PRODUCTION_UPGRADE_GUIDE.md "1.5 版升级指令书.md" docs/archive/deployment-history/
```

- [ ] **Step 4: 验证 deployment-history 归档结果**

Run: `find docs/archive/deployment-history -maxdepth 1 -type f | sort`  
Expected: 上述 22 个文件均出现在 `docs/archive/deployment-history/`

- [ ] **Step 5: Commit**

```bash
git add docs/archive/deployment-history
git commit -m "chore: archive deployment history documents"
```

### Task 3: 更新 README 当前入口链接

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 写失败校验条件**

```bash
rg -n "RELEASE_NOTES_V1.1.md|RELEASE_NOTES_V1.1.1.md|RELEASE_NOTES_V1.2.md|PVE_LXC_DEPLOYMENT_GUIDE.md" README.md
```

- [ ] **Step 2: 运行校验以确认旧链接存在**

Run: 上述 `rg` 命令  
Expected: README 仍引用旧根目录路径

- [ ] **Step 3: 修改 README 链接**

```markdown
- `RELEASE_NOTES_V1.1.md` -> `docs/archive/root-history/RELEASE_NOTES_V1.1.md`
- `RELEASE_NOTES_V1.1.1.md` -> `docs/archive/root-history/RELEASE_NOTES_V1.1.1.md`
- `RELEASE_NOTES_V1.2.md` -> `docs/archive/root-history/RELEASE_NOTES_V1.2.md`
- `PVE_LXC_DEPLOYMENT_GUIDE.md` -> `docs/archive/deployment-history/PVE_LXC_DEPLOYMENT_GUIDE.md`
```

- [ ] **Step 4: 验证 README 不再引用旧路径**

Run: `rg -n "RELEASE_NOTES_V1.1.md|RELEASE_NOTES_V1.1.1.md|RELEASE_NOTES_V1.2.md|PVE_LXC_DEPLOYMENT_GUIDE.md" README.md`  
Expected: 命中行仅包含 `docs/archive/` 新路径

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update readme archive links"
```

### Task 4: 做整体验证并记录结果

**Files:**
- Modify: `docs/reports/2026-04-07-remediation-optimization-report.md`

- [ ] **Step 1: 运行归档后根目录验证**

Run: `find . -maxdepth 1 -type f | sed 's#^\\./##' | sort`  
Expected: 历史文档显著减少，当前入口文档仍保留在根目录

- [ ] **Step 2: 运行整体验证**

Run: `git status --short`  
Expected: 体现为历史文档从根目录删除并在 `docs/archive/` 下新增，不包含当前运行入口文件误删

- [ ] **Step 3: 回写整改报告**

```markdown
- 已完成根目录历史文档归档：
  - `docs/archive/root-history/`
  - `docs/archive/deployment-history/`
- 已同步修正 `README.md` 入口链接
```

- [ ] **Step 4: 验证报告包含归档进展**

Run: `rg -n "archive/root-history|archive/deployment-history|README.md" docs/reports/2026-04-07-remediation-optimization-report.md`  
Expected: 命中新增归档说明

- [ ] **Step 5: Commit**

```bash
git add docs/reports/2026-04-07-remediation-optimization-report.md
git commit -m "docs: record root document archive progress"
```
