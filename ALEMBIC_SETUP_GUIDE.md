# Alembic 数据库迁移配置指南

## 为什么需要 Alembic？

当前项目使用 `Base.metadata.create_all()` 直接创建数据库表，这在以下场景会出现问题：

1. **无法修改已存在的表结构**：添加/删除字段、修改字段类型等
2. **无法追踪数据库变更历史**：不知道数据库经历了哪些变更
3. **无法回滚数据库变更**：出问题时无法恢复到之前的状态
4. **多环境部署困难**：开发、测试、生产环境数据库结构可能不一致

---

## 集成 Alembic 步骤

### 步骤 1：安装 Alembic

```bash
cd backend
pip install alembic
pip freeze > requirements.txt
```

更新 `backend/requirements.txt`：
```txt
alembic==1.13.1
```

---

### 步骤 2：初始化 Alembic

```bash
cd backend
alembic init alembic
```

这会创建以下文件结构：
```
backend/
├── alembic/
│   ├── env.py           # Alembic 环境配置
│   ├── script.py.mako   # 迁移脚本模板
│   └── versions/        # 迁移脚本目录
└── alembic.ini          # Alembic 配置文件
```

---

### 步骤 3：配置 alembic.ini

编辑 `backend/alembic.ini`：

```ini
# alembic.ini

[alembic]
# 迁移脚本目录
script_location = alembic

# 迁移脚本模板
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# 时区设置
timezone = Asia/Shanghai

# 数据库连接（从环境变量读取）
# 注意：这里使用 psycopg2，不是 asyncpg
sqlalchemy.url = postgresql://%(POSTGRES_USER)s:%(POSTGRES_PASSWORD)s@%(DB_HOST)s:%(DB_PORT)s/%(POSTGRES_DB)s

[post_write_hooks]
# 自动格式化生成的迁移脚本
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 100 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

### 步骤 4：配置 env.py

编辑 `backend/alembic/env.py`：

```python
"""Alembic Environment Configuration"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入配置和模型
from app.config import settings
from app.database import Base

# 导入所有模型（确保 Alembic 能检测到所有表）
from app.models.user import User
from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.models.expense import Expense
from app.models.audit_log import AuditLog

# Alembic Config object
config = context.config

# 从环境变量设置数据库连接
# 注意：Alembic 使用同步驱动，需要将 asyncpg 替换为 psycopg2
db_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://",
    "postgresql://"
)

# 设置环境变量供 alembic.ini 使用
os.environ["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "lh_admin")
os.environ["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "LanHai2024Secure!")
os.environ["DB_HOST"] = os.getenv("DB_HOST", "localhost")
os.environ["DB_PORT"] = os.getenv("DB_PORT", "5432")
os.environ["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "lh_contract_db")

# 或者直接设置 sqlalchemy.url
config.set_main_option("sqlalchemy.url", db_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 target_metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # 检测字段类型变更
        compare_server_default=True,  # 检测默认值变更
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 检测字段类型变更
            compare_server_default=True,  # 检测默认值变更
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

### 步骤 5：安装 psycopg2（Alembic 需要同步驱动）

```bash
cd backend
pip install psycopg2-binary
pip freeze > requirements.txt
```

更新 `backend/requirements.txt`：
```txt
psycopg2-binary==2.9.9
```

---

### 步骤 6：创建初始迁移

```bash
cd backend

# 创建初始迁移脚本
alembic revision --autogenerate -m "Initial migration - create all tables"

# 查看生成的迁移脚本
ls -la alembic/versions/
```

这会在 `alembic/versions/` 目录下生成一个迁移脚本，例如：
```
20251218_0915_abc123_initial_migration_create_all_tables.py
```

---

### 步骤 7：检查迁移脚本

打开生成的迁移脚本，检查 `upgrade()` 和 `downgrade()` 函数：

```python
"""Initial migration - create all tables

Revision ID: abc123
Revises: 
Create Date: 2025-12-18 09:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'abc123'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        # ... 其他字段
        sa.PrimaryKeyConstraint('id')
    )
    # ... 其他表
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ... 其他表
    # ### end Alembic commands ###
```

---

### 步骤 8：应用迁移

```bash
cd backend

# 查看当前数据库版本
alembic current

# 查看待应用的迁移
alembic history

# 应用所有迁移
alembic upgrade head

# 或者应用到特定版本
alembic upgrade abc123
```

---

### 步骤 9：修改 database.py（可选）

如果使用 Alembic，可以移除 `create_all()` 调用：

```python
# backend/app/database.py

async def init_db():
    """Initialize database - Alembic handles migrations"""
    # 注释掉自动创建表的代码
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    # 可以添加健康检查
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    
    print("Database connection verified. Use 'alembic upgrade head' to apply migrations.")
```

---

## 日常使用流程

### 1. 修改模型后创建迁移

```bash
cd backend

# 修改 app/models/*.py 中的模型
# 然后生成迁移脚本
alembic revision --autogenerate -m "Add new field to contract table"

# 检查生成的迁移脚本
cat alembic/versions/20251218_xxxx_add_new_field_to_contract_table.py

# 应用迁移
alembic upgrade head
```

---

### 2. 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade abc123

# 回滚所有迁移
alembic downgrade base
```

---

### 3. 查看迁移历史

```bash
# 查看所有迁移历史
alembic history

# 查看当前版本
alembic current

# 查看详细信息
alembic history --verbose
```

---

### 4. 手动创建迁移（不使用 autogenerate）

```bash
# 创建空白迁移脚本
alembic revision -m "Custom migration"

# 手动编辑生成的脚本
```

---

## Docker 环境中使用 Alembic

### 方法 1：在容器中执行

```bash
# 进入后端容器
docker-compose exec backend bash

# 在容器中执行迁移
cd /app
alembic upgrade head
```

---

### 方法 2：修改 Dockerfile 自动执行

```dockerfile
# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Waiting for database..."\n\
sleep 5\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the application
CMD ["/app/entrypoint.sh"]
```

---

### 方法 3：使用 docker-compose 启动脚本

创建 `backend/scripts/docker-entrypoint.sh`：

```bash
#!/bin/bash
set -e

echo "Waiting for database..."
sleep 5

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

修改 `docker-compose.prod.yml`：

```yaml
backend:
  # ...
  entrypoint: ["/app/scripts/docker-entrypoint.sh"]
```

---

## 常见问题

### Q1: Alembic 无法检测到模型变更

**原因：** 模型没有被导入到 `alembic/env.py`

**解决：**
```python
# alembic/env.py
from app.models.user import User
from app.models.contract_upstream import ContractUpstream
# ... 导入所有模型
```

---

### Q2: 迁移时出现 "Target database is not up to date"

**原因：** 数据库中的 alembic_version 表与代码不一致

**解决：**
```bash
# 查看当前版本
alembic current

# 强制设置版本（谨慎使用）
alembic stamp head
```

---

### Q3: 如何处理已存在的数据库？

**方法 1：** 创建初始迁移并标记为已应用
```bash
# 1. 创建初始迁移
alembic revision --autogenerate -m "Initial migration"

# 2. 不执行迁移，直接标记为已应用
alembic stamp head
```

**方法 2：** 备份数据，删除数据库，重新创建
```bash
# 1. 备份数据
pg_dump -U lh_admin lh_contract_db > backup.sql

# 2. 删除数据库
docker-compose down -v

# 3. 重新启动并应用迁移
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

---

### Q4: 生产环境如何安全地应用迁移？

**建议流程：**

1. **在测试环境验证迁移**
```bash
# 测试环境
alembic upgrade head
# 验证功能正常
```

2. **备份生产数据库**
```bash
# 生产环境
docker-compose exec db pg_dump -U lh_admin lh_contract_db > /backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

3. **应用迁移**
```bash
# 生产环境
docker-compose exec backend alembic upgrade head
```

4. **验证迁移结果**
```bash
# 检查数据库结构
docker-compose exec backend alembic current

# 测试应用功能
curl http://localhost/health/detailed
```

5. **如果出问题，回滚**
```bash
# 回滚迁移
docker-compose exec backend alembic downgrade -1

# 或者恢复备份
docker-compose exec db psql -U lh_admin lh_contract_db < /backups/backup_20251218_091500.sql
```

---

## 总结

### 使用 Alembic 的优势

✅ **版本控制**：数据库变更可追踪、可回滚  
✅ **团队协作**：多人开发时数据库结构同步  
✅ **生产安全**：增量迁移，避免数据丢失  
✅ **自动化**：可集成到 CI/CD 流程  

### 不使用 Alembic 的风险

❌ **数据丢失**：`create_all()` 不会修改已存在的表  
❌ **结构不一致**：多环境数据库结构可能不同  
❌ **无法回滚**：出问题时只能手动修复  
❌ **难以维护**：数据库变更历史不清晰  

---

## 下一步

1. **立即集成 Alembic**（推荐）
   - 按照本指南步骤 1-8 操作
   - 创建初始迁移
   - 在开发环境测试

2. **或者明确现有方案的限制**
   - 在部署文档中说明不支持数据库结构变更
   - 提供手动迁移 SQL 脚本
   - 定期备份数据库

**建议：** 对于正式生产环境，强烈建议集成 Alembic！
