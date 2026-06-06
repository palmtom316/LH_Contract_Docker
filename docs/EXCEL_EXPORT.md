# Excel 导出功能说明文档

## 概述

本系统的 Excel 导出功能使用前端 `file-saver` 库配合后端 `StreamingResponse` 实现跨浏览器兼容的文件下载。

## 技术实现

### 前端实现

**使用的库：**
- `file-saver` - 用于跨浏览器兼容的文件下载

**核心代码位置：**
- `/frontend/src/utils/download.js` - 统一的下载工具函数
- `/frontend/src/api/contractUpstream.js` - API 调用（包含 `responseType: 'blob'`）

**下载工具函数：**
```javascript
import { saveAs } from 'file-saver'

export function downloadExcel(data, filename) {
    const mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    const blob = new Blob([data], { type: mimeType })
    saveAs(blob, filename)
}

export function generateFilename(prefix, extension = 'xlsx') {
    const date = new Date().toISOString().slice(0, 10)
    return `${prefix}_${date}.${extension}`
}
```

**使用示例：**
```javascript
import { downloadExcel, generateFilename } from '@/utils/download'
import { exportContracts } from '@/api/contractUpstream'

const handleExport = async () => {
  try {
    const res = await exportContracts(queryParams)
    const filename = generateFilename('上游合同导出', 'xlsx')
    downloadExcel(res, filename)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败: ' + e.message)
  }
}
```

### 后端实现

**技术栈：**
- `pandas` + `openpyxl` - Excel 文件生成
- `StreamingResponse` - 流式响应

**核心代码位置：**
- `/backend/app/routers/contracts_upstream.py` - 上游合同导出
- `/backend/app/routers/contracts_downstream.py` - 下游合同导出
- `/backend/app/routers/contract_management.py` - 管理合同导出

**后端导出示例：**
```python
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import urllib.parse

@router.get("/export/excel", response_class=StreamingResponse)
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # 查询数据
    query = select(ContractUpstream)
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    # 转换为 DataFrame
    data = [{"合同编号": c.contract_code, ...} for c in contracts]
    df = pd.DataFrame(data)
    
    # 写入内存中的 Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Contracts')
    output.seek(0)
    
    # 生成带中文的文件名（使用 RFC 5987 编码）
    filename = f"上游合同列表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    encoded_filename = urllib.parse.quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )
```

## 已知问题与解决方案

### Chrome 浏览器文件名显示为 UUID

**问题描述：**
在 Chrome 浏览器中，下载的 Excel 文件名可能显示为类似 `965a6c3f-a51f-4c27-8e72-0f6364b86b3e` 的 UUID，而不是正确的中文文件名。

**原因：**
Chrome 的 **Parallel downloading（并行下载）** 实验性功能在启用状态下，可能无法正确解析服务器返回的 `Content-Disposition` 头中使用 UTF-8 编码的中文文件名。

**解决方法：**

1. 在 Chrome 地址栏输入：`chrome://flags/#enable-parallel-downloading`
2. 找到 **Parallel downloading** 选项
3. 将其设置为 **Disabled**（禁用）
4. 点击页面底部的 **Relaunch**（重新启动）按钮

**备注：**
- Microsoft Edge 不受此问题影响
- Firefox 不受此问题影响
- 这是 Chrome 的已知 bug，与代码实现无关

## API 请求配置

确保 API 请求正确配置 `responseType: 'blob'`：

```javascript
// /frontend/src/api/contractUpstream.js
export function exportContracts(params) {
    return request({
        url: '/contracts/upstream/export/excel',
        method: 'get',
        params,
        responseType: 'blob'  // 重要！必须设置
    })
}
```

## 响应拦截器配置

确保 Axios 响应拦截器正确处理 blob 响应：

```javascript
// /frontend/src/utils/request.js
service.interceptors.response.use(
    response => {
        // 对于 blob 响应，直接返回数据
        if (response.config.responseType === 'blob') {
            return response.data
        }
        return response.data
    },
    // ... error handling
)
```

## 文件清单

| 文件路径 | 说明 |
|---------|------|
| `/frontend/src/utils/download.js` | 下载工具函数 |
| `/frontend/src/api/contractUpstream.js` | 上游合同 API |
| `/frontend/src/api/contractDownstream.js` | 下游合同 API |
| `/frontend/src/api/contractManagement.js` | 管理合同 API |
| `/backend/app/routers/contracts_upstream.py` | 上游合同导出端点 |
| `/backend/app/routers/contracts_downstream.py` | 下游合同导出端点 |
| `/backend/app/routers/contract_management.py` | 管理合同导出端点 |

## 更新日志

- **2025-12-13**: 创建文档，记录 Chrome Parallel downloading 问题及解决方案
