from fastapi import APIRouter, BackgroundTasks, Depends, File, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.permissions import Permission, require_permission
from app.models.user import User
from app.schemas.bank_receipt import BankReceiptBatchResponse, BankReceiptItemResponse, ReceiptAllocationCreate, ReceiptAllocationResponse, ClearReceiptRequest, BankReceiptReviewUpdate
from app.services.bank_receipt import BankReceiptService
from app.models.bank_receipt import BankReceiptItem
from app.config import settings
from app.core.minio import get_minio_client

router=APIRouter()
def service(db: AsyncSession=Depends(get_db)): return BankReceiptService(db)

@router.post("/batches", response_model=BankReceiptBatchResponse, status_code=status.HTTP_201_CREATED)
async def upload(background_tasks:BackgroundTasks,file: UploadFile=File(...), user: User=Depends(require_permission(Permission.CREATE_PAYMENTS)), svc: BankReceiptService=Depends(service)):
    batch=await svc.upload(file,user); background_tasks.add_task(process_batch,batch.id); return batch
async def process_batch(batch_id:int):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db: await BankReceiptService(db).process(batch_id)
@router.get("/batches", response_model=list[BankReceiptBatchResponse])
async def batches(user: User=Depends(require_permission(Permission.VIEW_PAYMENTS)), svc: BankReceiptService=Depends(service)): return await svc.batches()
@router.get("/batches/{batch_id}/items", response_model=list[BankReceiptItemResponse])
async def items(batch_id:int,user: User=Depends(require_permission(Permission.VIEW_PAYMENTS)),svc: BankReceiptService=Depends(service)): return await svc.items(batch_id)
@router.get("/contracts/search")
async def contracts(q:str,direction:str,user: User=Depends(require_permission(Permission.VIEW_PAYMENTS)),svc: BankReceiptService=Depends(service)): return await svc.search(q,direction)
@router.post("/items/{item_id}/allocations", response_model=ReceiptAllocationResponse)
async def allocation(item_id:int,data:ReceiptAllocationCreate,user: User=Depends(require_permission(Permission.CREATE_PAYMENTS)),svc: BankReceiptService=Depends(service)): return await svc.allocate(item_id,data)
@router.put("/items/{item_id}/allocations/{allocation_id}", response_model=ReceiptAllocationResponse)
async def update_allocation(item_id:int,allocation_id:int,data:ReceiptAllocationCreate,user:User=Depends(require_permission(Permission.EDIT_PAYMENTS)),svc:BankReceiptService=Depends(service)): return await svc.update_allocation(item_id,allocation_id,data)
@router.delete("/items/{item_id}/allocations/{allocation_id}",status_code=204)
async def delete_allocation(item_id:int,allocation_id:int,user:User=Depends(require_permission(Permission.EDIT_PAYMENTS)),svc:BankReceiptService=Depends(service)): await svc.delete_allocation(item_id,allocation_id); return Response(status_code=204)
@router.put("/items/{item_id}",response_model=BankReceiptItemResponse)
async def review(item_id:int,data:BankReceiptReviewUpdate,user:User=Depends(require_permission(Permission.EDIT_PAYMENTS)),svc:BankReceiptService=Depends(service)):return await svc.review(item_id,data,user)
@router.post("/items/{item_id}/confirm", response_model=BankReceiptItemResponse)
async def confirm(item_id:int,user: User=Depends(require_permission(Permission.CREATE_PAYMENTS)),svc: BankReceiptService=Depends(service)): return await svc.confirm(item_id,user)
@router.post("/items/{item_id}/clear", response_model=BankReceiptItemResponse)
async def clear(item_id:int,data:ClearReceiptRequest,user: User=Depends(require_permission(Permission.DELETE_PAYMENTS)),svc: BankReceiptService=Depends(service)): return await svc.clear(item_id,data.reason,user)
@router.post("/items/{item_id}/ignore",response_model=BankReceiptItemResponse)
async def ignore(item_id:int,data:ClearReceiptRequest,user:User=Depends(require_permission(Permission.EDIT_PAYMENTS)),svc:BankReceiptService=Depends(service)):return await svc.ignore(item_id,data.reason,user)
@router.delete("/items/{item_id}",status_code=204)
async def delete_failed(item_id:int,user:User=Depends(require_permission(Permission.DELETE_PAYMENTS)),svc:BankReceiptService=Depends(service)):await svc.delete_failed(item_id,user);return Response(status_code=204)

@router.post("/items/{item_id}/retry",status_code=202)
async def retry(item_id:int,background_tasks:BackgroundTasks,user:User=Depends(require_permission(Permission.CREATE_PAYMENTS)),svc:BankReceiptService=Depends(service)):
    batch_id=await svc.retry(item_id,user);background_tasks.add_task(process_batch,batch_id);return {"status":"processing"}

@router.get("/items/{item_id}/file")
async def receipt_file(item_id:int,user:User=Depends(require_permission(Permission.VIEW_PAYMENTS)),db:AsyncSession=Depends(get_db)):
    item=await db.get(BankReceiptItem,item_id)
    if not item or not item.file_key:
        from app.core.errors import ResourceNotFoundError
        raise ResourceNotFoundError(resource_type="回单源文件",resource_id=item_id)
    response=get_minio_client().get_object(settings.MINIO_BUCKET_CONTRACTS,item.file_key)
    async def body():
        try:
            for chunk in response.stream(1024*1024): yield chunk
        finally: response.close();response.release_conn()
    return StreamingResponse(body(),media_type="application/pdf",headers={"Content-Disposition":f'inline; filename="receipt-{item.id}.pdf"'})
