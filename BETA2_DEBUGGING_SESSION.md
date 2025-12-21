# Beta2 本地调试环境状态

**创建时间**: 2025年12月15日 21:58  
**分支**: beta2  
**最新提交**: `3af1d54` - fix(backup): impl system/db backup & fix file download links

---

## ✅ 环境状态

### 1. Git 状态
- **当前分支**: `beta2`
- **状态**: 已与远程同步，工作区干净
- **最新提交**: 3af1d54 (2025-12-15 17:43:52)

### 2. 运行中的服务

| 服务 | 容器名 | 端口 | 状态 |
|------|--------|------|------|
| **数据库** | lh_contract_db | 5432 | ✅ Healthy |
| **后端** | lh_contract_backend | 8000 | ✅ Running |
| **前端** | lh_contract_frontend | 3000 | ✅ Running |

### 3. 服务访问地址

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:5432

### 4. 默认登录信息

```
用户名: admin
密码: admin123  (请查看 .env 文件确认)
```

---

## 📝 Beta2 版本主要更新

相比 `release/v1.0.0-beta` 分支，beta2 包含以下主要更新：

### 🆕 新增功能

1. **系统备份功能** (`backend/app/routers/system.py`)
   - 数据库备份
   - 系统备份
   - 文件下载链接修复

2. **审计日志** (`frontend/src/api/audit.js`)
   - 审计日志API
   - 系统操作记录

3. **增强的日志系统**
   - `backend/app/logs/app.log`
   - `backend/app/logs/error.log`

4. **调试工具**
   - `check_all_apis.py` - API检查工具
   - `check_api_data.py` - 数据检查
   - `check_users.py` - 用户检查
   - `debug_create_contract.py` - 合同创建调试

### 🔧 功能改进

1. **权限控制完善**
   - RBAC权限系统优化
   - 用户管理增强

2. **移动端适配**
   - 费用列表移动视图修复
   - 响应式设计改进

3. **导航优化**
   - 修复返回按钮循环问题
   - 组件卸载错误修复

4. **文件处理**
   - 文件下载链接修复
   - 上传路径优化

### 📁 主要文件变更

**后端变更**:
- ✨ 新增: `backend/app/routers/system.py` - 系统管理路由
- 📝 修改: 多个服务文件优化 (contract_*, expense_service)
- 🔧 改进: 异常处理和日志配置

**前端变更**:
- ✨ 新增: `frontend/src/api/system.js` - 系统API
- 📝 修改: `frontend/src/utils/request.js` - 请求工具优化
- 🎨 改进: 下游合同、管理合同列表视图

---

## 🛠️ 常用调试命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 查看数据库日志
docker-compose logs -f db

# 查看最后50行日志
docker-compose logs --tail=50 backend
```

### 服务控制

```bash
# 停止所有服务
docker-compose down

# 启动所有服务
docker-compose up -d

# 重启单个服务
docker-compose restart backend
docker-compose restart frontend

# 重新构建并启动
docker-compose up --build -d
```

### 数据库操作

```bash
# 连接数据库
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db

# 备份数据库
docker exec lh_contract_db pg_dump -U lh_admin lh_contract_db > backup.sql

# 恢复数据库
docker exec -i lh_contract_db psql -U lh_admin lh_contract_db < backup.sql
```

### 调试工具

```bash
# 检查所有API
python check_all_apis.py

# 检查用户数据
python check_users.py

# 调试合同创建
python debug_create_contract.py
```

### 进入容器调试

```bash
# 进入后端容器
docker exec -it lh_contract_backend /bin/sh

# 进入前端容器
docker exec -it lh_contract_frontend /bin/sh

# 进入数据库容器
docker exec -it lh_contract_db /bin/sh
```

---

## 🔍 调试检查清单

### 后端检查

- [ ] API健康检查: `curl http://localhost:8000/`
- [ ] API文档访问: `http://localhost:8000/docs`
- [ ] 数据库连接正常
- [ ] 日志文件正常写入
- [ ] 文件上传功能正常

### 前端检查

- [ ] 登录页面正常显示
- [ ] 路由导航正常
- [ ] API请求成功
- [ ] 移动端响应式正常
- [ ] 文件下载功能正常

### 数据库检查

- [ ] 数据库健康检查通过
- [ ] 表结构完整
- [ ] 默认管理员用户存在
- [ ] 数据持久化正常

---

## 🐛 常见问题排查

### 1. 服务启动失败

```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs backend
```

### 2. 数据库连接失败

```bash
# 检查数据库是否健康
docker exec lh_contract_db pg_isready -U lh_admin

# 检查环境变量
cat .env | grep DATABASE
```

### 3. 前端无法访问后端API

```bash
# 检查CORS配置
cat .env | grep CORS

# 检查网络连接
docker network ls
docker network inspect lh_contract_docker_lh_network
```

### 4. 文件上传失败

```bash
# 检查上传目录权限
ls -la backend/uploads/
ls -la uploads/

# 检查容器内上传目录
docker exec lh_contract_backend ls -la /app/uploads
```

---

## 📊 系统信息

```
Docker版本: 使用 docker-compose v3.8
Python版本: 3.11+
Node.js版本: 20+
PostgreSQL版本: 15-alpine
```

---

## 🎯 下一步操作建议

1. **测试登录功能**: 使用默认管理员账户登录
2. **检查核心功能**: 
   - 合同管理（上游、下游、管理类）
   - 费用管理
   - 用户权限
   - 审计日志
3. **测试新增功能**:
   - 系统备份功能
   - 文件下载
   - 移动端适配
4. **性能监控**: 观察日志文件，关注错误和警告

---

## 📞 支持

如遇问题，请查看：
- `backend/app/logs/` - 应用日志
- `docker-compose logs` - 容器日志
- `TROUBLESHOOTING.md` - 故障排查文档

**调试愉快！** 🚀
