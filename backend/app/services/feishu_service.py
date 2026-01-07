"""
Feishu (飞书) Open Platform Integration Service

This module provides integration with Feishu Open Platform for:
1. Syncing contract data to Feishu Base (多维表格)
2. Downloading approval PDFs
3. Getting tenant access tokens

Environment Variables Required:
- FEISHU_APP_ID: App ID from Feishu Open Platform
- FEISHU_APP_SECRET: App Secret from Feishu Open Platform
- FEISHU_BASE_APP_TOKEN: Base App Token (from Base URL)
- FEISHU_BASE_TABLE_ID: Table ID within the Base
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Feishu API Endpoints
FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"
TOKEN_URL = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
BASE_RECORDS_URL = f"{FEISHU_BASE_URL}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records"

# Environment Variables
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BASE_APP_TOKEN = os.getenv("FEISHU_BASE_APP_TOKEN", "")
FEISHU_BASE_TABLE_ID = os.getenv("FEISHU_BASE_TABLE_ID", "")


class FeishuService:
    """Feishu Open Platform API Client"""
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def get_tenant_access_token(self) -> str:
        """
        Get Tenant Access Token from Feishu.
        Caches the token until it expires.
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
            raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET must be set")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                json={
                    "app_id": FEISHU_APP_ID,
                    "app_secret": FEISHU_APP_SECRET
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"Failed to get Feishu token: {error_msg}")
                raise Exception(f"Feishu API Error: {error_msg}")
            
            self._access_token = data["tenant_access_token"]
            # Token expires in 7200 seconds (2 hours), refresh 5 minutes early
            expires_in = data.get("expire", 7200) - 300
            from datetime import timedelta
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained Feishu access token")
            return self._access_token
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        token = await self.get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def get_base_records(self, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get records from Feishu Base table
        """
        if not FEISHU_BASE_APP_TOKEN or not FEISHU_BASE_TABLE_ID:
            raise ValueError("FEISHU_BASE_APP_TOKEN and FEISHU_BASE_TABLE_ID must be set")
        
        url = BASE_RECORDS_URL.format(
            app_token=FEISHU_BASE_APP_TOKEN,
            table_id=FEISHU_BASE_TABLE_ID
        )
        
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def batch_create_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch create records in Feishu Base
        
        Args:
            records: List of record field dicts
        """
        if not FEISHU_BASE_APP_TOKEN or not FEISHU_BASE_TABLE_ID:
            raise ValueError("FEISHU_BASE_APP_TOKEN and FEISHU_BASE_TABLE_ID must be set")
        
        url = BASE_RECORDS_URL.format(
            app_token=FEISHU_BASE_APP_TOKEN,
            table_id=FEISHU_BASE_TABLE_ID
        ) + "/batch_create"
        
        headers = await self._get_headers()
        payload = {"records": [{"fields": r} for r in records]}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def batch_update_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch update records in Feishu Base
        
        Args:
            records: List of dicts with 'record_id' and 'fields' keys
        """
        if not FEISHU_BASE_APP_TOKEN or not FEISHU_BASE_TABLE_ID:
            raise ValueError("FEISHU_BASE_APP_TOKEN and FEISHU_BASE_TABLE_ID must be set")
        
        url = BASE_RECORDS_URL.format(
            app_token=FEISHU_BASE_APP_TOKEN,
            table_id=FEISHU_BASE_TABLE_ID
        ) + "/batch_update"
        
        headers = await self._get_headers()
        payload = {"records": records}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def download_file(self, file_token: str, save_path: str) -> str:
        """
        Download a file from Feishu (e.g., approval PDF)
        
        Args:
            file_token: The file token from Feishu
            save_path: Local path to save the file
            
        Returns:
            The saved file path
        """
        url = f"{FEISHU_BASE_URL}/drive/v1/files/{file_token}/download"
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded file to {save_path}")
            return save_path


# Singleton instance
feishu_service = FeishuService()


async def sync_contracts_to_base():
    """
    Main sync function: Syncs local contracts to Feishu Base
    
    Logic:
    1. Fetch all contracts from local DB
    2. Fetch existing records from Feishu Base
    3. Compare and batch create/update
    """
    logger.info("Starting contract sync to Feishu Base...")
    
    try:
        # Import here to avoid circular imports
        from app.database import async_session
        from app.models.contract_upstream import ContractUpstream
        from sqlalchemy import select
        
        async with async_session() as session:
            # Get all upstream contracts
            result = await session.execute(select(ContractUpstream))
            contracts = result.scalars().all()
            
            logger.info(f"Found {len(contracts)} upstream contracts to sync")
            
            # Get existing records from Feishu Base
            try:
                existing_data = await feishu_service.get_base_records()
                existing_records = existing_data.get("data", {}).get("items", [])
                logger.info(f"Found {len(existing_records)} existing records in Feishu Base")
            except Exception as e:
                logger.warning(f"Could not fetch existing Feishu records: {e}")
                existing_records = []
            
            # Build a map of contract_code -> record_id for updates
            existing_map = {}
            for record in existing_records:
                fields = record.get("fields", {})
                code = fields.get("合同编号")
                if code:
                    existing_map[code] = record.get("record_id")
            
            # Prepare records for create/update
            to_create = []
            to_update = []
            
            for contract in contracts:
                fields = {
                    "合同编号": contract.contract_code,
                    "合同名称": contract.contract_name,
                    "甲方单位": contract.party_a_name,
                    "乙方单位": contract.party_b_name,
                    "合同金额": float(contract.contract_amount or 0),
                    "合同状态": contract.status,
                    "签约日期": contract.sign_date.isoformat() if contract.sign_date else None,
                }
                
                if contract.contract_code in existing_map:
                    to_update.append({
                        "record_id": existing_map[contract.contract_code],
                        "fields": fields
                    })
                else:
                    to_create.append(fields)
            
            # Batch operations
            if to_create:
                logger.info(f"Creating {len(to_create)} new records in Feishu Base")
                await feishu_service.batch_create_records(to_create)
            
            if to_update:
                logger.info(f"Updating {len(to_update)} existing records in Feishu Base")
                await feishu_service.batch_update_records(to_update)
            
            logger.info("Contract sync completed successfully")
            
    except Exception as e:
        logger.error(f"Contract sync failed: {e}", exc_info=True)
        # Don't re-raise - we don't want to crash the worker
