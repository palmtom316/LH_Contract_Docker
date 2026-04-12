# 2026-04-11 安全审计报告

## 范围

- 后端：`backend/app`
- 前端：`frontend/src`、`frontend/public`
- 部署与代理：`docker-compose*.yml`、`nginx/*`
- 配套栈：`supabase/*`

本报告最初基于静态代码审计与配置检查形成，后续已补充 remediation 落地状态与自动化验证结果。

## 当前状态

状态：`v1-6-2-remediation` worktree 中的整改已合并回主线，自动化验证已完成，生产环境人工冒烟仍需单独执行。

### 已修复项

- Refresh token 可直接充当 access token 使用。
  状态：已修复
  证据：`backend/tests/test_auth.py`、`backend/tests/test_refresh_token.py`

- 改密后未撤销既有 refresh token。
  状态：已修复
  证据：`backend/tests/test_auth_hardening.py`

- 已登录用户可绕过对象级授权访问业务文件，且生产 `/uploads/` 可被直接公开访问。
  状态：已修复
  证据：`backend/tests/test_file_compatibility.py`、`backend/tests/test_file_authorization.py`

- 飞书 webhook 事件回调缺少完整鉴权。
  状态：已修复
  证据：`backend/tests/test_feishu_webhook_security.py`

- 上游 Excel 导入与 dashboard 趋势接口权限弱于同类接口。
  状态：已修复
  证据：`backend/tests/test_permission_hardening.py`

- 应用正常启动路径仍隐含 schema 修复动作，发布文档引用了错误的服务切换路径。
  状态：已修复
  证据：`backend/tests/test_release_contract.py`

- 前端将 refresh token 落盘到 `localStorage`，且诊断页会暴露本地鉴权材料。
  状态：已修复
  证据：`frontend/src/utils/__tests__/authSession.spec.js`、`npm --prefix frontend run build`

## 自动化验证摘要

- 后端鉴权/文件访问/刷新令牌相关验证：`18 passed, 28 skipped`
- 前端 `authSession` 测试：`2 passed`
- 前端生产构建：通过

## 原始发现摘要

### P0

- Refresh token 可直接充当 access token 使用。
- 文件下载接口只校验登录，不校验对象级授权。
- 生产 Nginx 直接公开上传目录。

### P1

- 飞书 Webhook 事件回调缺少有效鉴权。
- 上游合同 Excel 导入接口权限失控。
- 改密后未撤销既有 refresh token。

### P2

- 仪表盘趋势接口绕过 `VIEW_DASHBOARD` 权限。
- 前端将 access token 与 refresh token 存入 `localStorage`。
- 默认弱凭据和开发回退值仍广泛存在。
- 零星用工可能绕过“仅本人数据”限制。

### P3

- 生产对外公开 API 文档。

## 剩余发布门禁

- 仍需对生产或预发环境执行人工冒烟验证。
- 默认弱凭据与开发回退值清理、零星用工数据隔离边界确认仍应继续跟踪。
