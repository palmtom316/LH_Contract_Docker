from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime
import pandas as pd
import io
import urllib.parse

from app.database import get_db
from app.core.permissions import require_permission, Permission
from app.core.errors import DatabaseError
from app.models.user import User
from app.schemas.zero_hour_labor import (
    ZeroHourLaborCreate,
    ZeroHourLaborUpdate,
    ZeroHourLaborListResponse,
    ZeroHourLaborResponse
)
from app.services.zero_hour_labor_service import ZeroHourLaborService

router = APIRouter()

@router.get("/export/excel", response_class=StreamingResponse)
async def export_zero_hour_labor(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    attribution: Optional[str] = None,
    upstream_contract_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_EXPENSES))
):
    """Export zero hour labor to Excel"""
    try:
        service = ZeroHourLaborService(db)
        result = await service.list(
            page=1,
            page_size=10000,  # Get all records
            start_date=start_date,
            end_date=end_date,
            attribution=attribution,
            upstream_contract_id=upstream_contract_id,
            keyword=keyword
        )
        
        items = result["items"]
        
        # Create DataFrame with one row per material (or one row if no materials)
        data = []
        for item in items:
            base_row = {
                "用工时间": item.labor_date,
                "归属": "项目用工" if item.attribution == "PROJECT" else "公司用工",
                "上游合同": item.upstream_contract.contract_name if item.upstream_contract else "",
                "派工单位": item.dispatch_unit or "",
                "技工单价": float(item.skilled_unit_price or 0),
                "技工数量": float(item.skilled_quantity or 0),
                "技工合价": float(item.skilled_price_total or 0),
                "普工单价": float(item.general_unit_price or 0),
                "普工数量": float(item.general_quantity or 0),
                "普工合价": float(item.general_price_total or 0),
                "用车单价": float(item.vehicle_unit_price or 0),
                "用车数量": float(item.vehicle_quantity or 0),
                "用车合价": float(item.vehicle_price_total or 0),
            }
            
            if item.materials and len(item.materials) > 0:
                for mat in item.materials:
                    row = base_row.copy()
                    row["零星材料名称"] = mat.material_name
                    row["材料单位"] = mat.material_unit or ""
                    row["材料数量"] = float(mat.material_quantity or 0)
                    row["材料单价"] = float(mat.material_unit_price or 0)
                    row["材料合价"] = float(mat.material_price_total or 0)
                    row["零星用工价格合计"] = float(item.total_amount or 0)
                    data.append(row)
            else:
                row = base_row.copy()
                row["零星材料名称"] = ""
                row["材料单位"] = ""
                row["材料数量"] = 0
                row["材料单价"] = 0
                row["材料合价"] = 0
                row["零星用工价格合计"] = float(item.total_amount or 0)
                data.append(row)
        
        df = pd.DataFrame(data)
        
        # Save to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='零星用工')
        output.seek(0)
        
        filename = f"零星用工_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise DatabaseError(message="导出失败", detail=str(e))

@router.get("", response_model=ZeroHourLaborListResponse)
async def list_zero_hour_labor(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    attribution: Optional[str] = None,
    upstream_contract_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_EXPENSES))
):
    service = ZeroHourLaborService(db)
    return await service.list(
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        attribution=attribution,
        upstream_contract_id=upstream_contract_id,
        keyword=keyword
    )

@router.post("", response_model=ZeroHourLaborResponse, status_code=status.HTTP_201_CREATED)
async def create_zero_hour_labor(
    data_in: ZeroHourLaborCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CREATE_EXPENSES))
):
    service = ZeroHourLaborService(db)
    return await service.create(data_in, current_user)

@router.put("/{id}", response_model=ZeroHourLaborResponse)
async def update_zero_hour_labor(
    id: int,
    data_in: ZeroHourLaborUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EDIT_EXPENSES))
):
    service = ZeroHourLaborService(db)
    return await service.update(id, data_in, current_user)

@router.delete("/{id}")
async def delete_zero_hour_labor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DELETE_EXPENSES))
):
    service = ZeroHourLaborService(db)
    await service.delete(id, current_user)
    return {"status": "success"}
