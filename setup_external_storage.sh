#!/bin/bash

# ==========================================
# LH Contract System - Storage Expansion Script
# ==========================================
# This script automates the process of formatting a new disk,
# mounting it, and configuring the Docker system to use it.
#
# RUN THIS SCRIPT INSIDE YOUR LINUX VM AS ROOT
# Usage: sudo ./setup_external_storage.sh
# ==========================================

# Configuration
MOUNT_POINT="/mnt/data"
Start_Dir=$(pwd)
ENV_FILE="${Start_Dir}/.env"
# The default path where docker-compose expects uploads locally
LOCAL_UPLOAD_DIR="${Start_Dir}/backend/uploads"
# The new path on the big disk
NEW_UPLOAD_DIR="${MOUNT_POINT}/contract_uploads"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LH Contract Storage Expansion Setup ===${NC}"

# Check for root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (sudo ./setup_external_storage.sh)${NC}"
  exit 1
fi

# 1. Disk Selection
echo -e "\n${YELLOW}--- Step 1: Disk Selection ---${NC}"
echo "Detected Disks:"
lsblk -e 7 # Exclude loop devices
echo ""
echo -e "${YELLOW}Please identify the NEW disk added from PVE (e.g., /dev/sdb)${NC}"
read -p "Enter device path: " DISK_DEVICE

if [ ! -b "$DISK_DEVICE" ]; then
    echo -e "${RED}Error: Device $DISK_DEVICE not found.${NC}"
    exit 1
fi

echo -e "\n${RED}WARNING: ALL DATA ON $DISK_DEVICE WILL BE ERASED!${NC}"
read -p "Are you absolutely sure you want to format $DISK_DEVICE? (Type 'yes' to confirm): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 1
fi

# 2. Format and Mount
echo -e "\n${YELLOW}--- Step 2: Formatting and Mounting ---${NC}"
echo "Formatting $DISK_DEVICE to ext4..."
mkfs.ext4 -F "$DISK_DEVICE"

echo "Creating mount point at $MOUNT_POINT..."
mkdir -p "$MOUNT_POINT"

echo "Mounting disk..."
mount "$DISK_DEVICE" "$MOUNT_POINT"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Mount successful.${NC}"
else
    echo -e "${RED}Mount failed.${NC}"
    exit 1
fi

# 3. Persistence (fstab)
echo -e "\n${YELLOW}--- Step 3: Configuring Auto-mount ---${NC}"
UUID=$(blkid -s UUID -o value "$DISK_DEVICE")
if grep -q "$UUID" /etc/fstab; then
    echo "Entry already exists in /etc/fstab."
else
    echo "Adding UUID=$UUID to /etc/fstab..."
    echo "UUID=$UUID $MOUNT_POINT ext4 defaults 0 0" >> /etc/fstab
    echo -e "${GREEN}Done.${NC}"
fi

# 4. Data Migration
echo -e "\n${YELLOW}--- Step 4: Migrating Data ---${NC}"
echo "Creating upload directory at $NEW_UPLOAD_DIR..."
mkdir -p "$NEW_UPLOAD_DIR"

if [ -d "$LOCAL_UPLOAD_DIR" ] && [ "$(ls -A $LOCAL_UPLOAD_DIR)" ]; then
    echo "Copying existing files from $LOCAL_UPLOAD_DIR..."
    cp -r "$LOCAL_UPLOAD_DIR"/* "$NEW_UPLOAD_DIR"/
    echo -e "${GREEN}Files copied.${NC}"
else
    echo "No existing files to migrate or source directory empty."
fi

echo "Setting permissions (777 to avoid Docker permission issues)..."
chmod -R 777 "$NEW_UPLOAD_DIR"

# 5. Environment Configuration
echo -e "\n${YELLOW}--- Step 5: Updating Configuration ---${NC}"
if [ -f "$ENV_FILE" ]; then
    # Backup .env
    cp "$ENV_FILE" "${ENV_FILE}.bak"
    
    # Check if HOST_UPLOAD_DIR exists and replace it, otherwise append
    if grep -q "HOST_UPLOAD_DIR=" "$ENV_FILE"; then
        sed -i "s|^HOST_UPLOAD_DIR=.*|HOST_UPLOAD_DIR=$NEW_UPLOAD_DIR|" "$ENV_FILE"
    else
        echo "" >> "$ENV_FILE"
        echo "# External Storage Configuration" >> "$ENV_FILE"
        echo "HOST_UPLOAD_DIR=$NEW_UPLOAD_DIR" >> "$ENV_FILE"
    fi
    echo -e "${GREEN}Updated .env file with HOST_UPLOAD_DIR=$NEW_UPLOAD_DIR${NC}"
else
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    echo "Please manually set HOST_UPLOAD_DIR=$NEW_UPLOAD_DIR in your .env file."
fi

# 6. Apply Changes
echo -e "\n${YELLOW}--- Step 6: Restarting Application ---${NC}"
read -p "Do you want to restart Docker containers now to apply changes? (y/N): " RESTART_CONFIRM
if [[ "$RESTART_CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Stopping containers..."
    docker-compose down
    
    echo "Starting containers..."
    docker-compose up -d
    
    echo -e "\n${GREEN}=== SUCCESS! Storage expansion complete. ===${NC}"
    echo "Your files are now being saved to: $NEW_UPLOAD_DIR"
else
    echo -e "\n${GREEN}Setup complete.${NC}"
    echo "Remember to run 'docker-compose down && docker-compose up -d' later to apply changes."
fi
