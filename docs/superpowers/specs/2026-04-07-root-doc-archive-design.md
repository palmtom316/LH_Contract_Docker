# 2026-04-07 根目录历史文档归档设计

## 背景

当前仓库根目录混合了以下几类文件：

- 当前入口文档：`README.md`、`DEPLOYMENT.md`、`OPERATIONS_MANUAL.md`、`QUICK_REFERENCE.md`、`REQUIREMENTS.md`
- 当前运行与配置文件：`docker-compose*.yml`、`.env*.example`
- 历史发布说明：`RELEASE_NOTES_*`
- 历史升级指南：`UPGRADE_*`、`V1.5_*_GUIDE.md`、`1.5 版升级指令书.md`
- 历史审计/阶段/总结文档：`PHASE*`、`TECH_AUDIT*`、`*_REPORT.md`、`*_SUMMARY.md`
- 历史部署/环境排障指南：部分 `*_GUIDE.md`

这会带来两个问题：

1. 新进入项目的人很难区分“当前入口”和“历史资料”
2. 根目录噪音过高，真实运行入口被大量历史文档淹没

## 目标

- 收敛根目录，只保留当前版本直接使用的入口文档和运行配置
- 将明显历史性质的文档迁移到 `docs/archive/`
- 不改动业务代码
- 不重写历史文档正文，只修当前入口链接

## 非目标

- 不统一所有历史文档的内部交叉引用
- 不重构 `docs/` 现有业务文档结构
- 不修改运行脚本、部署脚本或 compose 配置的行为
- 不删除历史文档内容

## 方案选择

本次采用“中等归档”方案。

### 归档目录

新增两类归档目录：

- `docs/archive/root-history/`
- `docs/archive/deployment-history/`

### 保留在根目录的文件

以下文件继续保留在根目录，作为当前 1.6 的直接入口：

- `README.md`
- `DEPLOYMENT.md`
- `OPERATIONS_MANUAL.md`
- `QUICK_REFERENCE.md`
- `REQUIREMENTS.md`
- `TROUBLESHOOTING.md`
- `.env.example`
- `.env.production.example`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `docker-compose.prod.balanced.yml`
- `docker-compose.prod.lowmem.yml`
- `docker-compose.production.yml`
- `docker-compose.supabase.yml`
- 与当前运行直接相关的脚本：如 `setup_external_storage.sh`、`start_dev.ps1`

### 移动到 `docs/archive/root-history/` 的文件

这类文件属于版本演进记录、阶段总结、历史审计或一次性总结：

- `RELEASE_NOTES_V1.1.md`
- `RELEASE_NOTES_V1.1.1.md`
- `RELEASE_NOTES_V1.2.md`
- `ARCH_IMPROVEMENT_PLAN.md`
- `REVISED_ARCH_PLAN.md`
- `OPTIMIZATION_OVERVIEW.md`
- `AUDIT_COMPLETION_REPORT.md`
- `CODE_AUDIT_REPORT.md`
- `CODE_REVIEW_REPORT.md`
- `PHASE1_IMPLEMENTATION_SUMMARY.md`
- `PHASE2_IMPLEMENTATION_SUMMARY.md`
- `PHASE3_IMPLEMENTATION_SUMMARY.md`
- `TECH_AUDIT_REPORT_2024_12_30.md`
- `TECH_AUDIT_REPORT_2026_01_15.md`
- `TECH_AUDIT_V1.5.5.md`
- `BETA2_DEBUGGING_SESSION.md`
- `ERROR_HANDLING_APPLIED.md`
- `ERROR_HANDLING_EXTENDED.md`
- `PDF_VIEW_FIX.md`

### 移动到 `docs/archive/deployment-history/` 的文件

这类文件仍与部署/升级有关，但已明显偏历史版本、专项问题或阶段性迁移：

- `ALEMBIC_SETUP_GUIDE.md`
- `DAILY_OPS_MANUAL.md`
- `DEPLOYMENT_AND_MAINTENANCE_GUIDE.md`
- `DEPLOYMENT_CHECKLIST.md`
- `DEPLOYMENT_PVE_LXC.md`
- `GITHUB_UPLOAD_GUIDE.md`
- `LXC_PROXY_SETUP_GUIDE.md`
- `LXC_SSH_TROUBLESHOOTING.md`
- `OPS_STORAGE_EXPANSION_GUIDE.md`
- `PORT_CONFIGURATION_GUIDE.md`
- `PVE_LXC_DEPLOYMENT_GUIDE.md`
- `SSL_CERTIFICATE_GUIDE.md`
- `UPGRADE_GUIDE_V1.4.1_TO_V1.5.0.md`
- `UPGRADE_SAFETY_PROTOCOL.md`
- `UPGRADE_V1.1_TO_V1.2.md`
- `UPGRADE_V1.2.md`
- `UPGRADE_V1.3_TO_V1.3.2.md`
- `UPGRADE_V1.4.2.md`
- `V1.5.1_TO_V1.5.3_UPGRADE_GUIDE.md`
- `V1.5_COMPLETE_UPGRADE_GUIDE.md`
- `V1.5_PRODUCTION_UPGRADE_GUIDE.md`
- `1.5 版升级指令书.md`

## 链接修复范围

只修“当前入口文档”的链接，不全面回写所有历史文档。

本次需要同步更新：

- `README.md`

更新原则：

- 历史资料链接改为指向 `docs/archive/root-history/` 或 `docs/archive/deployment-history/`
- 对仍保留在根目录的当前文档，链接保持不变
- 历史文档内部的相互引用允许暂时保留旧路径，不作为本次阻塞项

## 验证方式

执行后验证以下事项：

1. `README.md` 中所有历史资料链接都能指向新位置
2. 根目录文件数量明显下降，入口文件保留完整
3. `rg` 检查当前入口文档不再引用旧路径
4. `git status --short` 能清晰反映移动结果，没有误删当前运行文件

## 风险与约束

- 历史文档内部仍可能存在旧路径引用，这是接受的技术债，不在本次清理范围内
- 不能误移动 `DEPLOYMENT.md`、`OPERATIONS_MANUAL.md`、`QUICK_REFERENCE.md` 这类当前仍在 README 中直接使用的入口文档
- 不能触碰业务代码、测试代码和运行配置

## 预期结果

- 根目录聚焦为“当前入口 + 当前配置 + 当前运行文件”
- 历史资料集中进入 `docs/archive/`
- README 成为清晰的一层导航，不再把根目录当历史档案馆使用
