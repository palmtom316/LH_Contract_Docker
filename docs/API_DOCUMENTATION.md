# API 文档

## 概述

合同管理系统提供了完整的 RESTful API，支持所有核心业务功能。

## 访问方式

### 在线文档

系统运行后，可通过以下地址访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### OpenAPI 规范

完整的 OpenAPI 3.0 规范文件：

- **JSON 格式**: [openapi.json](./openapi.json)
- **在线访问**: http://localhost:8000/openapi.json

## 认证

所有需要认证的 API 端点都使用 JWT Bearer Token 认证：

```bash
# 登录获取 token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=<username>" \
  --data-urlencode "password=<password>"

# 使用 token 访问受保护的端点
curl -X GET "http://localhost:8000/api/v1/contracts/upstream" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 主要端点分类

### 1. 认证与用户管理
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/change-password` - 修改密码
- `GET /api/v1/users/` - 获取用户列表（管理员）
- `POST /api/v1/users/` - 创建用户（管理员）

### 2. 上游合同管理
- `GET /api/v1/contracts/upstream` - 获取上游合同列表
- `POST /api/v1/contracts/upstream` - 创建上游合同
- `GET /api/v1/contracts/upstream/{id}` - 获取合同详情
- `PUT /api/v1/contracts/upstream/{id}` - 更新合同
- `DELETE /api/v1/contracts/upstream/{id}` - 删除合同
- `GET /api/v1/contracts/upstream/export` - 导出合同数据
- `POST /api/v1/contracts/upstream/import` - 导入合同数据

### 3. 下游合同管理
- `GET /api/v1/contracts/downstream` - 获取下游合同列表
- `POST /api/v1/contracts/downstream` - 创建下游合同
- `GET /api/v1/contracts/downstream/{id}` - 获取合同详情
- `PUT /api/v1/contracts/downstream/{id}` - 更新合同
- `DELETE /api/v1/contracts/downstream/{id}` - 删除合同

### 4. 管理合同
- `GET /api/v1/contracts/management` - 获取管理合同列表
- `POST /api/v1/contracts/management` - 创建管理合同
- `GET /api/v1/contracts/management/{id}` - 获取合同详情
- `PUT /api/v1/contracts/management/{id}` - 更新合同
- `DELETE /api/v1/contracts/management/{id}` - 删除合同

### 5. 财务记录
- `POST /api/v1/contracts/upstream/{id}/receivables` - 添加应收款
- `POST /api/v1/contracts/upstream/{id}/invoices` - 添加发票
- `POST /api/v1/contracts/upstream/{id}/receipts` - 添加回款
- `POST /api/v1/contracts/upstream/{id}/settlements` - 添加结算

### 6. 数据报表
- `GET /api/v1/reports/dashboard` - 获取仪表板数据
- `GET /api/v1/reports/contracts/summary` - 合同汇总报表
- `GET /api/v1/reports/finance/summary` - 财务汇总报表
- `GET /api/v1/reports/export` - 导出报表

### 7. 系统管理
- `GET /api/v1/system/config` - 获取系统配置
- `POST /api/v1/system/config` - 更新系统配置（管理员）
- `GET /api/v1/system/backup/db` - 数据库备份（管理员）
- `GET /api/v1/system/backup/full` - 完整系统备份（管理员）
- `POST /api/v1/system/reset` - 系统重置（管理员）
- `GET /api/v1/system/options` - 获取字典选项
- `POST /api/v1/system/options` - 创建字典选项（管理员）

### 8. 文件管理
- `POST /api/v1/common/upload` - 上传文件
- `GET /uploads/{path}` - 访问上传的文件

### 9. 健康检查
- `GET /health` - 基础健康检查
- `GET /health/detailed` - 详细健康检查
- `GET /health/db` - 数据库健康检查
- `GET /health/redis` - Redis 健康检查

## 响应格式

### 成功响应

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

### 错误响应

```json
{
  "error_code": "2001",
  "message": "合同不存在",
  "detail": "未找到ID为123的合同"
}
```

## 分页参数

大多数列表端点支持以下分页参数：

- `page`: 页码（从1开始）
- `page_size`: 每页数量（默认10，最大100）
- `keyword`: 搜索关键词
- `status`: 状态筛选

示例：
```bash
GET /api/v1/contracts/upstream?page=1&page_size=20&keyword=测试&status=执行中
```

## 权限说明

API 端点根据用户角色有不同的访问权限：

- **ADMIN（管理员）**: 所有权限
- **CONTRACT_MANAGER（合同管理）**: 合同和财务记录的完整权限
- **FINANCE（财务部）**: 财务记录和报表权限
- **ENGINEERING（工程部）**: 查看合同和部分财务权限
- **AUDIT（审计部）**: 查看和结算权限
- **BIDDING（投标部）**: 仅查看上游合同基本信息
- **GENERAL_AFFAIRS（综合部）**: 无合同费用和管理合同财务权限
- **COMPANY_LEADER（公司领导）**: 查看报表和概况权限

## 速率限制

为保护系统安全，部分端点实施了速率限制：

- 登录端点: 5次/分钟
- 一般API: 100次/分钟

超出限制将返回 `429 Too Many Requests` 错误。

## 示例代码

### Python

```python
import requests

# 登录
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "<username>", "password": "<password>"}
)
token = response.json()["access_token"]

# 获取合同列表
headers = {"Authorization": f"Bearer {token}"}
contracts = requests.get(
    "http://localhost:8000/api/v1/contracts/upstream",
    headers=headers
).json()
```

### JavaScript

```javascript
// 登录
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: '<username>', password: '<password>' })
});
const { access_token } = await loginResponse.json();

// 获取合同列表
const contractsResponse = await fetch('http://localhost:8000/api/v1/contracts/upstream', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const contracts = await contractsResponse.json();
```

## 更新日志

- **2025-12-21**: 添加系统重置功能文档
- **2025-12-16**: V1.1 版本发布，新增健康检查端点
- **2025-12-01**: V1.0 初始版本

## 技术支持

如有问题，请联系：
- 邮箱: support@example.com
- GitHub Issues: https://github.com/yourusername/LH_Contract_Docker/issues

### 电子发票导入

- `POST /api/v1/invoice-imports/batches` 上传发票批次 zip
- `GET /api/v1/invoice-imports/batches` 查看导入批次
- `GET /api/v1/invoice-imports/batches/{batch_id}/items` 查看批次发票明细
- `POST /api/v1/invoice-imports/items/{item_id}/allocations` 新增分摊
- `PUT /api/v1/invoice-imports/allocations/{allocation_id}` 修改分摊
- `POST /api/v1/invoice-imports/items/{item_id}/confirm` 确认挂账
- `POST /api/v1/invoice-imports/items/{item_id}/ignore` 忽略已识别但不处理的发票（须填写原因）
- `POST /api/v1/invoice-imports/items/{item_id}/clear` 清除已挂账发票（保留正式记录与审计快照）
- `DELETE /api/v1/invoice-imports/items/{item_id}` 仅删除未入账的失败文件

### 银行回单识别入账

- `POST /api/v1/bank-receipts/batches` 上传单份 PDF 回单并异步识别
- `GET /api/v1/bank-receipts/batches`、`GET /api/v1/bank-receipts/batches/{id}/items` 查询批次和明细
- `PUT /api/v1/bank-receipts/items/{id}` 人工复核方向、交易时间、金额和流水号
- `GET /api/v1/bank-receipts/contracts/search?q=<名称片段>&direction=receipt|payment` 按方向模糊查合同
- `POST /api/v1/bank-receipts/items/{id}/allocations` 添加分摊；收款仅上游，付款可下游或管理合同
- `PUT /api/v1/bank-receipts/items/{id}/allocations/{allocation_id}`、`DELETE /api/v1/bank-receipts/items/{id}/allocations/{allocation_id}` 修改或删除尚未确认的草稿分摊
- `POST /api/v1/bank-receipts/items/{id}/confirm` 等额分摊后确认入账
- `POST /api/v1/bank-receipts/items/{id}/clear` 清除入账并保留原记录、原因和审计历史
- `POST /api/v1/bank-receipts/items/{id}/ignore` 忽略不处理的回单；`DELETE /api/v1/bank-receipts/items/{id}` 仅删除失败文件

### MinerU 配置与操作规则

管理员在“系统配置 → 银行回单识别”中设置 MinerU 地址、Key、超时和公司银行账号。Key 只以掩码状态返回，数据库中以 `CONFIG_ENCRYPTION_KEY` 加密值保存。测试连接不会接受前端提供的地址，识别服务仅调用受控配置地址。

成功识别的发票/回单必须先人工复核并完成等额分摊才会写入正式表。清除不是物理删除：历史正式记录标为 `cleared`，原始文件、来源关系、清除原因和审计日志均保留；清除后可重新分摊确认。

### 零星用工财务详情

- `GET /api/v1/zero-hour-labor/{id}/detail` 查询基本信息、成本构成、应付款、挂账、付款及金额汇总
- `POST /api/v1/zero-hour-labor/{id}/payables|invoices|payments` 新增对应财务明细
- `PUT /api/v1/zero-hour-labor/{id}/finance/payables|invoices|payments/{record_id}` 修改对应财务明细
- `DELETE /api/v1/zero-hour-labor/{id}/finance/{kind}/{record_id}` 删除手工财务明细；主记录存在挂账或付款时禁止直接删除
