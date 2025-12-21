
@router.post("/reset")
async def reset_system(
    confirm_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reset system to initial state.
    WARNING: This will delete ALL data except superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Need admin privileges")
        
    if confirm_code != "RESET":
        raise HTTPException(status_code=400, detail="Invalid confirmation code")

    try:
        # 1. Truncate business tables
        # Execute raw SQL for truncation to be faster and cleaner
        # Be careful with Foreign Key constraints, use CASCADE
        tables = [
             "contract_upstream_settlement", "contract_upstream_receipt", "contract_upstream_invoice", "contract_upstream_receivable",
             "contract_downstream_settlement", "contract_downstream_payment", "contract_downstream_invoice", "contract_downstream_payable",
             "contract_management_settlement", "contract_management_payment", "contract_management_invoice", "contract_management_payable",
             "contract_upstream", "contract_downstream", "contract_management",
             "sys_expenses", "sys_audit_log", "sys_files", "sys_dictionary", "sys_config"
        ]
        
        # We need to preserve non-contract related data? 
        # Requirement says: "清空所有合同、用户（保留管理员）及相关数据" matches.
        
        # Truncate tables
        from sqlalchemy import text
        for table in tables:
             # Check if table exists first? Or just try truncate is fine if we know schema
             try:
                 await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
             except Exception as e:
                 print(f"Truncate {table} error (might not exist): {e}")

        # 2. Delete Users (except superusers)
        # Assuming current_user is superuser, we keep them. 
        # Or keep ALL superusers?
        await db.execute(text("DELETE FROM users WHERE is_superuser = false"))
        
        # 3. Clear Uploads Directory (except system logo possibly?)
        # Be careful not to delete 'system' folder if we want to keep logo, but 'reset' usually means clean slate.
        # User requirement says "System Reset", implies clean state.
        # Let's clean everything in uploads except maybe 'system' folder if we want to be nice?
        # A true reset deletes everything.
        
        uploads_dir = settings.UPLOAD_DIR
        for item in os.listdir(uploads_dir):
             item_path = os.path.join(uploads_dir, item)
             if item == 'system':
                  continue # Maybe keep system config/logos?
             if os.path.isfile(item_path):
                  os.unlink(item_path)
             elif os.path.isdir(item_path):
                  shutil.rmtree(item_path)

        await db.commit()
        return {"message": "System reset successfully"}

    except Exception as e:
        await db.rollback()
        print(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=f"System reset failed: {str(e)}")
