# 2026-04-08 品牌信息治理清单

## 立即治理
- frontend/src/views/Login.vue
- frontend/src/views/Layout.vue
- frontend/src/views/mobile/MobileLayout.vue
- frontend/src/router/index.js
- frontend/index.html
- frontend/src/stores/system.js
- frontend/src/views/system/SystemSettings.vue
- frontend/src/views/contracts/ManagementList.vue
- frontend/src/views/contracts/DownstreamList.vue
- backend/app/routers/system.py
- backend/app/routers/auth.py
- backend/app/routers/contracts_upstream.py

## 第二批治理
- backend/tests/test_api_integration.py
- backend/tests/test_contracts.py
- backend/app/generate_downstream_test_data.py
- backend/app/generate_management_test_data.py
- backend/app/generate_upstream_test_data.py
- frontend/src/views/contracts/__tests__/UpstreamList.spec.js

## 延后决策
- docker-compose*.yml 中 `lh_contract_*`
- .env*.example 中 `lh_contract_db`
- 仓库名 `LH_Contract_Docker`

## 保留项
- `lh_contract_db`: 与现网数据库、备份脚本、升级文档兼容，暂不修改
- `lh_contract_backend`: 与现网容器名称兼容，暂不修改
- `LH_Contract_Docker`: 仓库名与远端地址相关，需单独迁移评估

## 兼容性决策表

| 项目 | 当前值 | 动作 | 理由 |
| --- | --- | --- | --- |
| 仓库名 | `LH_Contract_Docker` | 暂不修改 | 涉及远端仓库迁移与地址变更 |
| 容器名 | `lh_contract_*` | 暂不修改 | 会影响运维脚本与现网部署 |
| 数据库名 | `lh_contract_db` | 暂不修改 | 会影响连接串、备份与升级脚本 |

## 验收结果
- 运行时品牌默认值: 已清理
- 导入模板品牌示例: 已清理
- 测试与脚本样例: 已清理
- 主文档品牌残留: 已清理
- 活跃脚本与技术文档中的硬编码品牌/敏感示例: 已清理主要风险项
- 兼容性命名: 已登记保留
