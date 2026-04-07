# Upgrade Guide: v1.3 to v1.3.2

This guide outlines the steps to upgrade your production environment from version 1.3 to 1.3.2.
It specifically addresses the need to protect **entered information (Database)** and **PDF files (Uploads)**.

## 1. Preparation & Backups (CRITICAL)

Before performing any upgrade, you MUST backup your data.

### 1.1 Backup Database (Entered Information)
Execute the following command to export the entire database to a SQL file.
Replace `postgres` with your actual database user if you changed it in `.env`.

```bash
# Verify the container name first
docker ps | grep db_prod 

# Perform Backup (Assuming container name is 'lh_contract_db_prod')
docker exec -t lh_contract_db_prod pg_dumpall -c -U postgres > dump_v1.3_backup_$(date +%Y%m%d).sql
```
*Check `dump_v1.3_backup_....sql` to ensure it is not empty.*

### 1.2 Backup Uploaded Files (PDFs)
Based on `docker-compose.prod.yml`, your uploads are stored in the host directory specified by `HOST_UPLOAD_DIR` (defaulting to `./uploads`).

```bash
# Create a compressed archive of the uploads directory
tar -czvf uploads_backup_v1.3_$(date +%Y%m%d).tar.gz ./uploads
```

### 1.3 Backup Configuration
```bash
cp .env.production .env.production.backup
cp docker-compose.prod.yml docker-compose.prod.yml.backup
```

---

## 2. Perform Upgrade

### 2.1 Get Upgrade Code
```bash
# Fetch latest updates
git fetch origin

# Switch to the new version tag/branch
git checkout release/V1.3.2
```

### 2.2 Verify Configuration
Check if there are any new environment variables in `.env.production.example` and update your `.env.production` if necessary.
*(Note: v1.3 to v1.3.2 is a minor patch, usually no config changes needed)*

### 2.3 Rebuild and Restart Services
We use `docker-compose.prod.yml` for production.

```bash
# Pull correct base images
docker-compose -f docker-compose.prod.yml pull

# Rebuild images (Frontend will now show Version 1.3.2)
docker-compose -f docker-compose.prod.yml build

# Restart services in detached mode
docker-compose -f docker-compose.prod.yml up -d
```

---

## 3. Verification

### 3.1 Check Service Status
```bash
docker-compose -f docker-compose.prod.yml ps
```
Ensure all containers (`db`, `redis`, `backend`, `frontend`, `nginx`) are `Up (healthy)`.

### 3.2 Verify Application
1. Open your browser and navigate to the system URL.
2. Login and check the sidebar footer. It should now display: **Version 1.3.2**.
3. **Verify Data**: Check a few contracts to ensure "Entered Information" is intact.
4. **Verify Files**: Try to download/preview a previously uploaded PDF to ensure file mapping is correct.

---

## 4. Rollback (If needed)

If something goes wrong, you can roll back to v1.3:

```bash
git checkout release/V1.3
docker-compose -f docker-compose.prod.yml up -d --build
```

If data was corrupted (unlikely), restore from backup:
```bash
# Restore DB
cat dump_v1.3_backup_....sql | docker exec -i lh_contract_db_prod psql -U postgres

# Restore Files
# (Caution: this overwrites existing uploads)
tar -xzvf uploads_backup_v1.3_....tar.gz
```
