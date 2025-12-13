# 数据库修复总结

**日期**: 2025-12-13 14:14  
**问题**: 登录时出现网络错误

## 发现的问题

### 1. Email 验证错误
- **问题**: admin 用户的 email 字段存储的是电话号码 `18623100316`
- **原因**: 之前将 email 字段改为 phone，后来又改回来，但数据未清理
- **影响**: Pydantic EmailStr 验证失败，导致登录 500 错误

### 2. 角色枚举值不匹配
- **问题**: 数据库中有 7 个用户使用了扩展角色（leader, engineering, finance 等）
- **原因**: 用户管理模块测试时创建的用户
- **影响**: SQLAlchemy ENUM 验证失败

## 执行的修复

### 1. 修复 Admin 用户 Email
```sql
UPDATE users SET email = 'admin@lanhai.com' WHERE username = 'admin';
```

### 2. 修复其他用户角色
```sql
-- 将所有无效角色改为 VIEWER
UPDATE users SET role = 'VIEWER' 
WHERE role NOT IN ('ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER');
```

**影响的用户**: 7 个用户（zhanglu, wangyong, huangwenguo 等）

### 3. 重启后端服务
```bash
docker-compose restart backend
```

## 修复后的状态

### 用户数据
- **总用户数**: 8 个
- **Admin 用户**: 
  - 用户名: `admin`
  - Email: `admin@lanhai.com`
  - 角色: `ADMIN`
- **其他用户**: 7 个，角色均为 `VIEWER`

### 系统状态
- ✅ 后端服务正常运行
- ✅ Email 验证通过
- ✅ 角色枚举验证通过
- ✅ 登录功能恢复正常

## 登录信息

- **URL**: http://localhost:3000
- **用户名**: `admin`
- **密码**: `admin123`

## 注意事项

1. 其他 7 个用户的角色已被重置为 VIEWER
2. 如需这些用户有不同权限，需要手动更新其角色为 MANAGER 或 OPERATOR
3. 数据库中的业务数据（合同、费用等）未受影响

## 可用的 SQL 命令

### 查看所有用户
```sql
SELECT id, username, email, role, is_active FROM users ORDER BY id;
```

### 更新用户角色
```sql
-- 将用户改为 MANAGER
UPDATE users SET role = 'MANAGER' WHERE username = 'zhanglu';

-- 将用户改为 OPERATOR
UPDATE users SET role = 'OPERATOR' WHERE username = 'wangyong';
```

### 删除测试用户（如果需要）
```sql
-- 注意：如果用户有关联的业务数据，会因外键约束而失败
DELETE FROM users WHERE id > 1;
```
