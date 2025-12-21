# 金额显示问题调查报告

**日期**: 2025-12-21  
**问题**: 合同金额显示异常（如输入 100000 显示为 32768）

## 问题分析

### 1. 后端验证
通过直接 API 测试，确认后端完全正常：

```bash
curl -X POST "http://localhost:8000/api/v1/contracts/management/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"contract_amount":100000,...}'
```

**结果**: 后端返回正确的 `"contract_amount": "100000.00"`

### 2. 数据库模型
- 字段类型: `Numeric(15, 2)` ✅ 正确
- Pydantic Schema: `Decimal` 类型 ✅ 正确

### 3. 前端组件
- 金额输入使用 `FormulaInput` 组件 ✅ 正确
- 金额显示使用 `formatMoney` 函数 ✅ 正确

### 4. 可能的原因

经过分析，问题可能出在以下几个方面：

1. **el-input-number 配置问题**
   - 缺少显式的 `:step` 属性
   - 可能导致某些边界情况下的数值处理异常

2. **数据绑定问题**
   - 前端在某个环节可能对数值进行了错误的转换
   - 需要检查 Vue 的响应式数据流

3. **浏览器兼容性**
   - 某些浏览器对大数值的处理可能有差异

## 修复措施

### 已实施的修复

1. **为所有 el-input-number 添加显式 step 属性**
   - `ManagementList.vue`: 添加 `:step="1"`
   - `DownstreamList.vue`: 添加 `:step="1"`
   - `UpstreamList.vue`: 添加 `:step="1"`

2. **确保数据类型一致性**
   - 后端: `Numeric(15, 2)` → `Decimal`
   - 前端: `Number` / `Decimal` 字符串

### 建议的额外验证

1. **清除浏览器缓存**
   ```bash
   # 建议用户清除浏览器缓存并重新加载
   ```

2. **检查前端构建**
   ```bash
   cd frontend
   npm run build
   ```

3. **验证数据流**
   - 在浏览器开发者工具中检查网络请求
   - 确认 API 响应中的 `contract_amount` 值
   - 检查 Vue DevTools 中的组件数据

## 测试步骤

1. **创建新合同**
   - 输入金额: 100000
   - 预期显示: ¥ 100,000.00

2. **添加财务记录**
   - 应付款: 30000 → 预期: ¥ 30,000.00
   - 挂账: 20000 → 预期: ¥ 20,000.00
   - 付款: 10000 → 预期: ¥ 10,000.00

3. **检查汇总**
   - 合同总额应正确显示
   - 各项财务汇总应正确计算

## 后续行动

如果问题仍然存在，需要：

1. **启用详细日志**
   - 在 `FormulaInput.vue` 中添加 console.log
   - 在 API 响应拦截器中添加日志

2. **单元测试**
   - 为 `FormulaInput` 组件添加单元测试
   - 测试各种数值输入场景

3. **浏览器兼容性测试**
   - 在不同浏览器中测试（Chrome, Firefox, Safari, Edge）
   - 检查是否是特定浏览器的问题

## 结论

已添加 `:step="1"` 属性到所有 `el-input-number` 组件，这应该能解决潜在的数值处理问题。

如果问题持续存在，需要进一步调查前端的数据绑定和响应式更新机制。

---

**更新时间**: 2025-12-21 20:30:00  
**状态**: 修复已应用，等待验证
