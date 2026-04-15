"""
Feishu Webhook Router

Handles callbacks from Feishu Open Platform for:
- Approval instance status changes
- PDF download triggers

Environment Variables:
- FEISHU_WEBHOOK_VERIFICATION_TOKEN: Token for verifying webhook requests
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

FEISHU_WEBHOOK_VERIFICATION_TOKEN = os.getenv("FEISHU_WEBHOOK_VERIFICATION_TOKEN", "")


class FeishuWebhookEvent(BaseModel):
    """Feishu webhook event schema"""
    schema_version: Optional[str] = None
    header: Optional[dict] = None
    event: Optional[dict] = None
    # For URL verification challenge
    challenge: Optional[str] = None
    token: Optional[str] = None
    type: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response for Feishu webhooks"""
    challenge: Optional[str] = None
    msg: str = "success"


def _verify_feishu_event(body: dict) -> None:
    """Require the configured Feishu verification token on every callback."""
    if not FEISHU_WEBHOOK_VERIFICATION_TOKEN:
        logger.error("Feishu webhook verification token is not configured")
        if settings.DEBUG:
            return
        raise HTTPException(status_code=503, detail="Feishu webhook verification is not configured")

    if body.get("token") != FEISHU_WEBHOOK_VERIFICATION_TOKEN:
        logger.warning("Webhook token verification failed")
        raise HTTPException(status_code=403, detail="Invalid token")


async def download_approval_pdf(instance_code: str, contract_id: int, contract_type: str):
    """
    Background task to download approval PDF from Feishu
    
    Args:
        instance_code: Feishu approval instance code
        contract_id: Local contract ID
        contract_type: Contract type (upstream, downstream, management)
    """
    logger.info(f"Downloading approval PDF for {contract_type} contract {contract_id}")
    
    try:
        from app.services.feishu_service import feishu_service
        from app.database import async_session
        from sqlalchemy import update
        
        # Import the appropriate model
        if contract_type == "upstream":
            from app.models.contract_upstream import ContractUpstream as ContractModel
            table_name = "contracts_upstream"
        elif contract_type == "downstream":
            from app.models.contract_downstream import ContractDownstream as ContractModel
            table_name = "contracts_downstream"
        else:
            from app.models.contract_management import ContractManagement as ContractModel
            table_name = "contracts_management"
        
        # TODO: Implement actual PDF download when Feishu provides the file token
        # For now, just update the approval status
        # file_token = await get_approval_pdf_token(instance_code)
        # save_path = f"/app/uploads/approvals/{contract_type}_{contract_id}.pdf"
        # await feishu_service.download_file(file_token, save_path)
        
        # Update contract with approval status
        async with async_session() as session:
            stmt = (
                update(ContractModel)
                .where(ContractModel.id == contract_id)
                .values(approval_status="APPROVED")
            )
            await session.execute(stmt)
            await session.commit()
            
        logger.info(f"Updated approval status for {contract_type} contract {contract_id}")
        
    except Exception as e:
        logger.error(f"Failed to process approval PDF: {e}", exc_info=True)


@router.post("/webhook")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Feishu webhook events
    
    Supports:
    1. URL Verification (challenge-response)
    2. Approval status change events
    """
    try:
        body = await request.json()
        logger.info(f"Received Feishu webhook: {body.get('type', 'event')}")
        
        # Handle URL verification challenge
        if body.get("type") == "url_verification":
            challenge = body.get("challenge")
            if not challenge:
                raise HTTPException(status_code=400, detail="Missing challenge")

            _verify_feishu_event(body)
            logger.info("URL verification successful")
            return {"challenge": challenge}

        _verify_feishu_event(body)

        # Handle event callbacks
        header = body.get("header", {})
        event_type = header.get("event_type", "")
        
        if event_type == "approval.instance.status_changed":
            event = body.get("event", {})
            instance_code = event.get("instance_code")
            status = event.get("status")
            
            logger.info(f"Approval status changed: {instance_code} -> {status}")
            
            if status == "APPROVED":
                # Find the contract by instance code and trigger PDF download
                # This is a simplified version - in production, you'd query the DB
                # to find which contract has this instance_code
                
                from app.database import async_session
                from app.models.contract_upstream import ContractUpstream
                from sqlalchemy import select
                
                async with async_session() as session:
                    result = await session.execute(
                        select(ContractUpstream)
                        .where(ContractUpstream.feishu_instance_code == instance_code)
                    )
                    contract = result.scalar_one_or_none()
                    
                    if contract:
                        background_tasks.add_task(
                            download_approval_pdf,
                            instance_code,
                            contract.id,
                            "upstream"
                        )
                        logger.info(f"Queued PDF download for contract {contract.id}")
                    else:
                        logger.warning(f"No contract found for instance code: {instance_code}")
        
        return {"msg": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        # Return success to prevent Feishu from retrying
        return {"msg": "error logged"}
