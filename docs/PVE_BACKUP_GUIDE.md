# PVE 虚拟机备份配置指南

**版本**: V1.0  
**更新日期**: 2025年12月  
**适用对象**: 系统管理员

---

## 目录

1. [备份策略规划](#1-备份策略规划)
2. [通过Web界面配置备份](#2-通过web界面配置备份)
3. [通过命令行配置备份](#3-通过命令行配置备份)
4. [备份恢复操作](#4-备份恢复操作)
5. [备份文件管理](#5-备份文件管理)
6. [最佳实践建议](#6-最佳实践建议)

---

## 1. 备份策略规划

### 1.1 推荐备份策略

| 备份类型 | 频率 | 保留数量 | 备份时间 | 备份模式 |
|----------|------|----------|----------|----------|
| **完整备份** | 每周日 | 4份 | 凌晨 02:00 | Snapshot |
| **增量备份**（如有PBS） | 每天 | 7份 | 凌晨 03:00 | Snapshot |

### 1.2 备份模式说明

| 模式 | 说明 | 停机时间 | 适用场景 |
|------|------|----------|----------|
| **Snapshot** | 快照备份 | 无（在线备份） | ✅ 推荐，生产环境 |
| **Suspend** | 暂停后备份 | 短暂暂停 | 对数据一致性要求高 |
| **Stop** | 停机后备份 | 需要停机 | 维护窗口期 |

### 1.3 压缩方式选择

| 压缩方式 | 压缩比 | 速度 | 推荐度 |
|----------|--------|------|--------|
| **zstd** | 高 | 快 | ⭐⭐⭐ 强烈推荐 |
| **lzo** | 中 | 很快 | ⭐⭐ 推荐 |
| **gzip** | 高 | 慢 | ⭐ 老旧环境 |
| **none** | 无压缩 | 最快 | 临时备份 |

---

## 2. 通过Web界面配置备份

### 2.1 创建定时备份任务

**步骤 1**: 登录 PVE Web 界面
```
https://[PVE主机IP]:8006
```

**步骤 2**: 进入备份设置
```
左侧导航 → Datacenter → Backup → Add
```

**步骤 3**: 配置备份参数

```
┌─────────────────────────────────────────────────────────────────┐
│  Create: Backup Job                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  General                                                        │
│  ──────────────────────────────────────────────                │
│                                                                 │
│  Node:            [All  ▼] 或选择特定节点                       │
│                                                                 │
│  Storage:         [local ▼]    ← 选择备份存储位置               │
│                                                                 │
│  Schedule:        [sun 02:00]  ← 每周日凌晨2点                  │
│                                                                 │
│  Selection mode:  [Include selected VMs ▼]                      │
│                                                                 │
│  ─────────────────────────────────────────────                 │
│  VM Selection                                                   │
│  ─────────────────────────────────────────────                 │
│                                                                 │
│  ☑ 100 (lh-contract-vm)   ← 勾选要备份的VM                     │
│  ☐ 101 (other-vm)                                               │
│                                                                 │
│  ─────────────────────────────────────────────                 │
│  Backup Options                                                 │
│  ─────────────────────────────────────────────                 │
│                                                                 │
│  Mode:            [Snapshot ▼]     ← 推荐使用快照模式           │
│                                                                 │
│  Compression:     [ZSTD ▼]         ← 推荐使用zstd压缩           │
│                                                                 │
│  ─────────────────────────────────────────────                 │
│  Retention                                                      │
│  ─────────────────────────────────────────────                 │
│                                                                 │
│  Keep Last:       [4]              ← 保留最近4份备份            │
│                                                                 │
│  ☑ Enable                          ← 启用此备份任务             │
│                                                                 │
│                              [Cancel]  [Create]                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**步骤 4**: 点击 **Create** 保存

### 2.2 手动执行备份

**步骤 1**: 选择要备份的 VM
```
左侧导航 → 节点名 → VM名称 (如: 100 lh-contract-vm)
```

**步骤 2**: 执行备份
```
右侧面板 → Backup → Backup now
```

**步骤 3**: 选择备份选项
```
┌─────────────────────────────────────────────────────────────────┐
│  Backup VM 100                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Storage:         [local ▼]                                     │
│                                                                 │
│  Mode:            [Snapshot ▼]                                  │
│                                                                 │
│  Compression:     [ZSTD ▼]                                      │
│                                                                 │
│  ☐ Send email to: [________________________]                    │
│                                                                 │
│  Notes:           [Weekly backup - 2025-12-26]                  │
│                                                                 │
│                              [Cancel]  [Backup]                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**步骤 4**: 点击 **Backup** 开始备份

### 2.3 查看备份进度

备份开始后，可在 **Task Viewer** 中查看进度：
```
左上角 → 查看运行中的任务
或
节点 → Task History
```

---

## 3. 通过命令行配置备份

### 3.1 手动备份命令

```bash
# SSH 登录到 PVE 主机
ssh root@[PVE_IP]

# 执行备份 (替换 100 为您的 VM ID)
vzdump 100 --mode snapshot --compress zstd --storage local --notes "Manual backup $(date +%Y-%m-%d)"
```

**常用参数说明**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--mode` | 备份模式 | `snapshot`, `suspend`, `stop` |
| `--compress` | 压缩方式 | `zstd`, `lzo`, `gzip`, `0`(无压缩) |
| `--storage` | 存储位置 | `local`, 或其他配置的存储名 |
| `--notes` | 备份备注 | `"Weekly backup"` |
| `--mailto` | 邮件通知 | `admin@example.com` |

### 3.2 查看现有备份任务

```bash
# 查看所有备份任务配置
cat /etc/pve/jobs.cfg

# 或使用 pvesh 命令
pvesh get /cluster/backup
```

### 3.3 通过命令行创建定时备份任务

```bash
# 创建备份任务 (每周日凌晨2点备份 VM 100)
pvesh create /cluster/backup \
  --vmid 100 \
  --schedule "sun 02:00" \
  --storage local \
  --mode snapshot \
  --compress zstd \
  --mailnotification failure \
  --prune-backups keep-last=4 \
  --enabled 1
```

### 3.4 使用 Crontab 定时备份

如果需要更灵活的控制，可以使用 crontab：

```bash
# 编辑 root 的 crontab
crontab -e

# 添加每周日凌晨2点备份 VM 100
0 2 * * 0 /usr/bin/vzdump 100 --mode snapshot --compress zstd --storage local --notes "Auto weekly backup" >> /var/log/vzdump-cron.log 2>&1
```

---

## 4. 备份恢复操作

### 4.1 通过 Web 界面恢复

**恢复到原 VM（覆盖）**：

1. 进入 **Datacenter** → **Storage** → **local** → **Backups**
2. 选择要恢复的备份文件
3. 点击 **Restore**
4. 确认 VM ID（默认会覆盖原VM）
5. 点击 **Restore** 开始恢复

```
┌─────────────────────────────────────────────────────────────────┐
│  Restore: vzdump-qemu-100-2025_12_22-02_00_00.vma.zst          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Target Storage:  [local-lvm ▼]    ← VM磁盘存储位置             │
│                                                                 │
│  VM ID:           [100]            ← 使用原ID会覆盖现有VM       │
│                                                                 │
│  ☐ Unique         ← 勾选可生成新的MAC地址                       │
│                                                                 │
│  ☐ Start after restore                                          │
│                                                                 │
│  Bandwidth Limit: [___________] MiB/s                           │
│                                                                 │
│                              [Cancel]  [Restore]                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**恢复到新 VM（保留原VM）**：

1. 在恢复对话框中，修改 **VM ID** 为新的未使用ID（如 101）
2. 勾选 **Unique** 选项（生成新的MAC地址）
3. 点击 **Restore**

### 4.2 通过命令行恢复

```bash
# 恢复到原 VM ID (会覆盖)
qmrestore /var/lib/vz/dump/vzdump-qemu-100-2025_12_22-02_00_00.vma.zst 100

# 恢复到新 VM ID
qmrestore /var/lib/vz/dump/vzdump-qemu-100-2025_12_22-02_00_00.vma.zst 101 --unique

# 指定存储位置
qmrestore /var/lib/vz/dump/vzdump-qemu-100-2025_12_22-02_00_00.vma.zst 101 --storage local-lvm
```

### 4.3 恢复后检查

```bash
# 启动恢复的 VM
qm start 100

# 检查 VM 状态
qm status 100

# 查看 VM 控制台（通过 Web 界面或 VNC）
```

---

## 5. 备份文件管理

### 5.1 查看备份文件

```bash
# 列出所有备份
ls -lh /var/lib/vz/dump/

# 查看备份详情
vzdump --help

# 按大小排序
ls -lhS /var/lib/vz/dump/*.vma*
```

### 5.2 删除旧备份

**通过 Web 界面**：
1. **Datacenter** → **Storage** → **local** → **Backups**
2. 选择要删除的备份
3. 点击 **Remove**

**通过命令行**：
```bash
# 删除指定备份文件
rm /var/lib/vz/dump/vzdump-qemu-100-2025_12_15-02_00_00.vma.zst
rm /var/lib/vz/dump/vzdump-qemu-100-2025_12_15-02_00_00.log
```

### 5.3 备份文件传输

**下载备份到本地**：
```bash
# 从本地电脑执行
scp root@[PVE_IP]:/var/lib/vz/dump/vzdump-qemu-100-*.vma.zst ./本地目录/
```

**上传备份到 PVE**：
```bash
# 上传备份文件
scp ./vzdump-qemu-100-*.vma.zst root@[PVE_IP]:/var/lib/vz/dump/

# 刷新 PVE 存储以识别新文件
pvesm scan local
```

### 5.4 查看备份空间使用

```bash
# 查看备份目录空间
du -sh /var/lib/vz/dump/

# 查看各备份文件大小
du -h /var/lib/vz/dump/*.vma* | sort -h
```

---

## 6. 最佳实践建议

### 6.1 备份策略建议

```
┌─────────────────────────────────────────────────────────────────┐
│                    合同管理系统 备份策略                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   第1层: 应用数据备份 (backup.sh)                               │
│   ──────────────────────────────                               │
│   • 频率: 每天凌晨 03:00                                        │
│   • 保留: 7天                                                   │
│   • 内容: 数据库 + 上传文件                                     │
│   • 位置: /backups/ (VM内部)                                    │
│                                                                 │
│   第2层: PVE 虚拟机备份                                         │
│   ──────────────────────────                                   │
│   • 频率: 每周日凌晨 02:00                                      │
│   • 保留: 4周                                                   │
│   • 内容: 完整VM镜像                                            │
│   • 位置: /var/lib/vz/dump/ (PVE主机)                           │
│                                                                 │
│   第3层: 异地备份 (可选)                                        │
│   ──────────────────────                                       │
│   • 频率: 每月                                                  │
│   • 方式: 将PVE备份复制到外部存储/NAS                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 备份检查清单

定期执行以下检查：

- [ ] 检查备份任务是否正常执行
- [ ] 验证备份文件完整性
- [ ] 确认备份空间充足
- [ ] 测试恢复流程（每季度一次）
- [ ] 更新备份文档

### 6.3 监控备份状态

```bash
# 查看最近的备份任务日志
cat /var/log/vzdump.log | tail -50

# 查看备份任务历史
pvesh get /cluster/tasks --typefilter vzdump

# 检查备份任务配置
cat /etc/pve/jobs.cfg
```

### 6.4 邮件通知配置

在 PVE 中配置邮件通知，以便备份失败时收到警报：

1. **Datacenter** → **Options** → **Email from address**
2. 配置 SMTP 服务器
3. 在备份任务中启用邮件通知

---

## 快速参考卡

### 常用命令

| 操作 | 命令 |
|------|------|
| 手动备份 | `vzdump 100 --mode snapshot --compress zstd` |
| 恢复备份 | `qmrestore /path/to/backup.vma.zst 100` |
| 列出备份 | `ls -lh /var/lib/vz/dump/` |
| 查看备份日志 | `cat /var/log/vzdump.log` |
| 启动 VM | `qm start 100` |
| 停止 VM | `qm stop 100` |
| VM 状态 | `qm status 100` |

### Web 界面路径

| 操作 | 路径 |
|------|------|
| 创建备份任务 | Datacenter → Backup → Add |
| 查看备份文件 | Storage → local → Backups |
| 手动备份 | VM → Backup → Backup now |
| 恢复备份 | Storage → Backups → 选择文件 → Restore |

---

**文档结束**

*本指南最后更新于 2025年12月*
