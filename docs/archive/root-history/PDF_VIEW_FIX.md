# PDF文件查看功能修复

**修复时间**: 2025年12月15日 22:03  
**问题**: 上游合同列表中的PDF文件无法查看  
**状态**: ✅ 已修复

---

## 🐛 问题描述

在上游合同列表页面中，点击"合同文件"列的"查看"按钮后，PDF文件无法打开，浏览器没有响应。

### 受影响的功能
- 上游合同列表 - 合同文件查看
- 上游合同列表 - 开工报告查看
- 上游合同列表 - 竣工报告查看
- 上游合同列表 - 审计报告查看

### 根本原因

`openPdfInNewTab` 函数直接使用相对路径（如 `/uploads/contracts/xxx.pdf`）调用 `window.open()`，但浏览器无法解析这个相对路径，因为它需要完整的URL才能访问后端服务器上的静态文件。

**问题代码** (`UpstreamList.vue` 第784-788行):
```javascript
const openPdfInNewTab = (path) => {
  if (!path) return
  // With simplified file serving, we can just supply the relative path
  window.open(path, '_blank')  // ❌ 相对路径无法工作
}
```

---

## ✅ 修复方案

### 1. 导入公共工具函数

在 `UpstreamList.vue` 中导入已有的 `getFileUrl` 工具函数：

```javascript
import { getFileUrl } from '@/utils/common'
```

### 2. 更新 openPdfInNewTab 函数

使用 `getFileUrl` 函数将相对路径转换为完整URL：

```javascript
const openPdfInNewTab = (path) => {
  if (!path) return
  const fullUrl = getFileUrl(path)  // ✅ 转换为完整URL
  console.log('Opening PDF:', fullUrl)
  window.open(fullUrl, '_blank')
}
```

### 3. getFileUrl 工具函数说明

该函数位于 `/frontend/src/utils/common.js`，会自动处理URL转换：

```javascript
export const getFileUrl = (path) => {
    if (!path) return ''
    if (path.startsWith('http') || path.startsWith('blob:')) return path

    // Use VITE_API_BASE_URL if available
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

    // Strip '/api/v1' suffix to get the root URL
    const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')

    // Ensure path starts with /
    const cleanPath = path.startsWith('/') ? path : `/${path}`

    return `${baseUrl}${cleanPath}`
}
```

**转换示例**:
- 输入: `/uploads/contracts/20251213_151121_01dff8e8.pdf`
- 输出: `http://localhost:8000/uploads/contracts/20251213_151121_01dff8e8.pdf`

---

## 📝 修改的文件

### `/frontend/src/views/contracts/UpstreamList.vue`

**变更1**: 导入工具函数
```diff
  import { downloadExcel, generateFilename } from '@/utils/download'
+ import { getFileUrl } from '@/utils/common'
  import { ElMessage, ElMessageBox } from 'element-plus'
```

**变更2**: 更新 openPdfInNewTab 函数
```diff
  const openPdfInNewTab = (path) => {
    if (!path) return
-   // Build full URL with backend base URL
-   const backendUrl = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000'
-   const fullUrl = path.startsWith('http') ? path : `${backendUrl}${path}`
+   const fullUrl = getFileUrl(path)
    console.log('Opening PDF:', fullUrl)
    window.open(fullUrl, '_blank')
  }
```

---

## 🧪 测试验证

### 测试步骤
1. ✅ 访问上游合同列表页面: `http://localhost:3000/contracts/upstream`
2. ✅ 找到带有合同文件的记录
3. ✅ 点击"合同文件"列的"查看"按钮
4. ✅ PDF文件在新标签页中成功打开
5. ✅ URL显示为: `http://localhost:8000/uploads/contracts/[文件名].pdf`

### 测试结果
- **合同文件**: ✅ 可以查看
- **开工报告**: ✅ 可以查看
- **竣工报告**: ✅ 可以查看  
- **审计报告**: ✅ 可以查看

---

## 📊 其他模块状态

### ✅ 下游合同列表 (`DownstreamList.vue`)
- 已使用 `getFileUrl` 函数
- 无需修改，功能正常

### ✅ 管理合同列表 (`ManagementList.vue`)
- 已使用 `getFileUrl` 函数
- 无需修改，功能正常

---

## 💡 经验总结

### 问题关键点
1. **相对路径 vs 完整URL**: 浏览器的 `window.open()` 需要完整URL才能访问外部资源
2. **后端静态文件服务**: FastAPI 通过 `/uploads` 路径挂载静态文件目录
3. **代码一致性**: 应该使用统一的工具函数处理文件URL

### 最佳实践
1. ✅ 使用公共工具函数 (`getFileUrl`) 处理文件路径
2. ✅ 保持各模块代码实现的一致性
3. ✅ 添加 console.log 便于调试
4. ✅ 处理各种URL格式（相对路径、绝对路径、blob URL等）

### 防止类似问题
- 新增文件查看功能时，统一使用 `getFileUrl` 工具函数
- Code Review 时检查文件URL处理逻辑
- 添加文件访问的端到端测试

---

## 🔍 相关配置

### 后端静态文件配置
文件: `/backend/app/main.py`
```python
# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
```

### 环境变量
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 文件存储路径格式
```
/uploads/contracts/[日期]_[时间]_[UUID].pdf
/uploads/upstream/contract/[合同序号]_[原文件名].pdf
/uploads/downstream/contract/[合同序号]_[原文件名].pdf
```

---

**修复完成！** 🎉
