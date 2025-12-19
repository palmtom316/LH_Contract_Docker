# PVE 虚拟机存储扩容与挂载指南

我们为您提供了一个自动化脚本 `setup_external_storage.sh` 来简化配置过程。您既可以使用脚本自动完成，也可以参考下方的“手动操作步骤”逐步执行。

## 🚀 方式一：使用自动化脚本（推荐）

该脚本会自动检测硬盘、格式化、挂载、迁移旧数据并更新 Docker 配置。

1. **在 PVE 中添加硬盘**：
   - 参考下方“手动操作步骤”中的“第一步”，在 PVE 管理界面为 VM 添加一块新硬盘（如 900G）。
   - **重启 VM** 以确保新硬盘被识别（或者如果在 VM 内能看到新盘也可以不重启）。

2. **在 VM 中运行脚本**：
   登录到 VM，进入项目目录，执行以下命令：
   ```bash
   # 给予执行权限
   chmod +x setup_external_storage.sh
   
   # 以 root 身份运行
   sudo ./setup_external_storage.sh
   ```

3. **按提示操作**：
   - 脚本会列出所有磁盘，请仔细确认哪个是新加的盘（如 `/dev/sdb`）。
   - 输入磁盘名称并确认格式化。
   - 脚本会自动完成剩余所有工作并重启服务。

---

## 🛠️ 方式二：手动操作步骤

如果您希望手动控制每一步，请按照以下流程操作：

## 第一步：在 PVE 中添加硬盘

1. 登录 Proxmox VE 管理界面。
2. 选择您的虚拟机 (VM)。
3. 点击 **硬件 (Hardware)** -> **添加 (Add)** -> **硬盘 (Hard Disk)**。
4. 设置磁盘大小（例如 `500G` 或 `900G`，建议留一点余量）。
5. 存储位置选择 `local-lvm` 或您那 1T 空间所在的存储池。
6. 点击 **添加 (Add)**。
   * *注意：大多数现代 Linux 系统支持热插拔，但建议重启一下 VM 确保识别。*

## 第二步：在 VM (Linux) 中格式化并挂载硬盘

登录到您的 VM 终端（SSH 或 控制台），执行以下操作：

1. **查找新硬盘名称**：
   ```bash
   lsblk
   # 通常会看到一个新的盘，比如 sdb 或 vdb，大小为您刚才设置的
   ```

2. **格式化硬盘** (假设新盘是 `/dev/sdb`)：
   ```bash
   mkfs.ext4 /dev/sdb
   ```

3. **创建挂载点**：
   ```bash
   mkdir -p /mnt/data
   ```

4. **挂载硬盘**：
   ```bash
   mount /dev/sdb /mnt/data
   ```

5. **设置开机自动挂载**：
   编辑 `/etc/fstab` 文件，添加一行：
   ```
   /dev/sdb    /mnt/data    ext4    defaults    0    0
   ```

6. **迁移现有数据 (如果已有上传文件)**：
   ```bash
   # 假设原来的代码在 /opt/LH_Contract_Docker
   # 创建新的上传目录
   mkdir -p /mnt/data/contract_uploads
   
   # 复制旧数据
   cp -r /opt/LH_Contract_Docker/backend/uploads/* /mnt/data/contract_uploads/
   
   # 设置权限 (确保 Docker 容器内的用户能读写，通常 1000:1000 或 777)
   chmod -R 777 /mnt/data/contract_uploads
   ```

## 第三步：修改 Docker 配置

我们已经修改了 `docker-compose.yml` 支持环境变量配置。您只需要在项目根目录的 `.env` 文件中指定新路径即可。

1. **编辑 .env 文件**：
   ```bash
   vim .env
   ```

2. **添加或修改 HOST_UPLOAD_DIR 变量**：
   ```env
   # 指向您刚才挂载的大硬盘目录
   HOST_UPLOAD_DIR=/mnt/data/contract_uploads
   ```

3. **重启 Docker 容器**：
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 验证

上传一个新文件，然后检查它是否出现在大硬盘中：
```bash
ls -l /mnt/data/contract_uploads
```

---
**优势**：
- **无需改动代码**：后端逻辑完全不用变。
- **数据分离**：代码在系统盘，数据在数据盘，系统重装也不丢数据。
- **灵活扩容**：未来如果 1T 不够了，PVE 可以直接对虚拟硬盘扩容，Linux 侧 `resize2fs` 即可生效。
