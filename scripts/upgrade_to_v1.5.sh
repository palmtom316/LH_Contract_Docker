#!/bin/bash
set -e

# LH_Contract_Docker V1.5 Upgrade Script
# Automated steps for upgrading from v1.4.1 to v1.5

echo "============================================="
echo "   LH_Contract_Docker V1.5 Upgrade Script    "
echo "============================================="

# 0. Environment Check
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found."
    exit 1
fi

# 1. Update Source Code
echo "Step 1: Updating Source Code..."
TARGET_VERSION=${1:-v1.5}
echo "Target Version: $TARGET_VERSION"

# Check if git is available
if command -v git &> /dev/null; then
    echo "Fetching latest changes..."
    git fetch --all --tags
    
    echo "Checking out $TARGET_VERSION..."
    git checkout $TARGET_VERSION || {
        echo "Error: Could not checkout $TARGET_VERSION. Please check if the tag/branch exists."
        read -p "Do you want to continue with current code? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    
    # If it's a branch, pull latest
    if git show-ref --verify --quiet refs/heads/$TARGET_VERSION; then
        echo "Pulling latest changes for branch $TARGET_VERSION..."
        git pull origin $TARGET_VERSION
    fi
else
    echo "⚠ Warning: 'git' command not found. Skipping code update."
fi

echo "Step 2: Checking Environment Configuration..."
# Ensure MinIO config exists in .env or config
if grep -q "MINIO_ENDPOINT" .env; then
    echo "✔ MinIO configuration found."
else
    echo "⚠ Warning: MINIO_ENDPOINT not found in .env. Using defaults or backend config."
fi

# 2. Update Containers (Enable MinIO)
echo "Step 3: Starting Services (Database & MinIO)..."
docker-compose up -d db minio redis
echo "Waiting for services to be healthy..."
sleep 10

# 3. Database Migration
echo "Step 4: Applying Database Schema Changes (Alembic)..."
# Ensure backend is running to run alembic
docker-compose up -d backend
docker-compose exec -T backend alembic upgrade head
echo "✔ Database schema updated."

# 4. File Migration (Dry Run)
echo "Step 5: Preparing for File Migration..."
# Copy scripts into container to ensure they are available
echo "Copying migration scripts to backend container..."
docker cp scripts/migrate_to_minio.py lh_contract_backend:/app/
docker cp scripts/verify_migration.py lh_contract_backend:/app/

echo "Running Migration Dry-Run..."
docker-compose exec -T backend python /app/migrate_to_minio.py --dry-run

echo "---------------------------------------------"
read -p "Dry run complete. Do you want to proceed with ACTUAL file migration? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Step 6: Executing File Migration..."
    docker-compose exec -T backend python /app/migrate_to_minio.py
    
    echo "Step 7: Verifying Migration..."
    docker-compose exec -T backend python /app/verify_migration.py
else
    echo "Skipping file migration execution."
fi

# 5. Frontend Upgrade
echo "Step 8: Rebuilding Frontend..."
docker-compose build frontend
docker-compose up -d frontend

echo "============================================="
echo "       Upgrade V1.5 Completed Successfully!   "
echo "============================================="
echo "Please verify by uploading a new file in the UI."
