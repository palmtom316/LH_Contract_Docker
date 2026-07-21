"""Bank receipt parsing, allocation and posting service."""
from datetime import datetime
from decimal import Decimal
from io import BytesIO
import hashlib, re, uuid
import httpx
from pypdf import PdfReader
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.errors import ResourceNotFoundError, ValidationError
from app.models.bank_receipt import BankReceiptBatch, BankReceiptItem, BankReceiptAllocation
from app.models.bank_receipt import BankReceiptMatchCandidate
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayment
from app.models.contract_management import ContractManagement, FinanceManagementPayment
from app.services.audit_service import create_audit_log
from app.config import settings
from app.core.minio import get_minio_client, ensure_bucket_exists
from app.models.system import SystemConfig

MONEY = re.compile(r"(?:币种及金额|交易金额|金额)[:：\s]*(?:CNY|RMB|人民币)?\s*[￥¥]?\s*([\d,]+\.\d{2})", re.IGNORECASE)
SERIAL = re.compile(r"(?:核心流水号|交易流水号|流水号)[:：\s]*([A-Za-z0-9_-]+)")
DATE_TIME = re.compile(r"(?:交易日期|交易时间)[:：\s]*(\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)")
FIELD_PATTERNS={"payer_name":re.compile(r"付款(?:人|方)(?:名称)?[:：\s]*([^\n\r]+)"),"payer_account":re.compile(r"付款(?:人|方)?账号[:：\s]*([\d\s-]+)"),"payee_name":re.compile(r"收款(?:人|方)(?:名称)?[:：\s]*([^\n\r]+)"),"payee_account":re.compile(r"收款(?:人|方)?账号[:：\s]*([\d\s-]+)"),"summary":re.compile(r"(?:摘要|用途)[:：\s]*([^\n\r]+)")}
CN_DIGITS={"零":0,"壹":1,"贰":2,"叁":3,"肆":4,"伍":5,"陆":6,"柒":7,"捌":8,"玖":9,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
CN_UNITS={"拾":10,"佰":100,"仟":1000,"万":10000,"亿":100000000,"十":10,"百":100,"千":1000}

def chinese_money_to_decimal(value:str|None):
    if not value:return None
    text=value.replace("人民币","").replace("整","")
    integer=re.split(r"[元圆]",text,1)[0]; total=section=number=0
    for char in integer:
        if char in CN_DIGITS:number=CN_DIGITS[char]
        elif char in CN_UNITS:
            unit=CN_UNITS[char]
            if unit<10000:section+=(number or 1)*unit
            else:total=(total+section+number)*unit;section=0
            number=0
    result=Decimal(total+section+number)
    jiao=re.search(r"([零壹贰叁肆伍陆柒捌玖一二三四五六七八九])角",value);fen=re.search(r"([零壹贰叁肆伍陆柒捌玖一二三四五六七八九])分",value)
    if jiao:result+=Decimal(CN_DIGITS[jiao.group(1)])/10
    if fen:result+=Decimal(CN_DIGITS[fen.group(1)])/100
    return result.quantize(Decimal("0.01"))

def parse_receipt_text(text: str) -> dict:
    """Conservative normalized extraction; unknown values stay reviewable."""
    amount_match, serial_match, time_match = MONEY.search(text or ""), SERIAL.search(text or ""), DATE_TIME.search(text or "")
    parsed = {"amount": Decimal(amount_match.group(1).replace(",", "")) if amount_match else None, "bank_serial_number": serial_match.group(1) if serial_match else None, "transaction_at": None}
    for key,pattern in FIELD_PATTERNS.items():
        match=pattern.search(text or "");parsed[key]=match.group(1).strip() if match else None
    chinese_match=re.search(r"(?:人民币)?(?:大写)?[:：\s]*([零壹贰叁肆伍陆柒捌玖拾佰仟万亿一二三四五六七八九十百千元圆角分整]+)",text or "")
    parsed["chinese_amount"]=chinese_money_to_decimal(chinese_match.group(1)) if chinese_match else None
    parsed["amount_consistent"]=parsed["chinese_amount"] is None or parsed["amount"] is None or parsed["chinese_amount"]==parsed["amount"]
    if time_match:
        normalized = time_match.group(1).replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")
        try: parsed["transaction_at"] = datetime.fromisoformat(normalized)
        except ValueError: pass
    return parsed

def determine_direction(company_accounts: set[str], payer_account: str | None, payee_account: str | None) -> str:
    clean = lambda value: re.sub(r"\s+", "", value or "")
    accounts = {clean(x) for x in company_accounts}
    payer, payee = clean(payer_account), clean(payee_account)
    if payee and payee in accounts and payer not in accounts: return "receipt"
    if payer and payer in accounts and payee not in accounts: return "payment"
    return "unknown"

def validate_receipt_allocation_total(amount, allocations):
    total = sum((Decimal(str(x)) for x in allocations), Decimal("0.00"))
    if amount is None or total.quantize(Decimal("0.01")) != Decimal(str(amount)).quantize(Decimal("0.01")):
        raise ValidationError(message="分摊金额合计必须等于回单金额", field_errors={"amount": "分摊金额必须精确等于回单金额"})

class BankReceiptService:
    def __init__(self, db: AsyncSession): self.db = db
    async def upload(self, upload, user):
        data = await upload.read()
        if not upload.filename.lower().endswith(".pdf") or not data.startswith(b"%PDF"):
            raise ValidationError(message="仅支持 PDF 银行回单")
        digest = hashlib.sha256(data).hexdigest()
        duplicate = await self.db.scalar(select(BankReceiptItem).where(BankReceiptItem.sha256 == digest))
        if duplicate: raise ValidationError(message="该回单已导入", field_errors={"file": f"原记录 #{duplicate.id}"})
        if len(data) > settings.MAX_FILE_SIZE: raise ValidationError(message="回单文件超过大小限制")
        pages=max(1,len(re.findall(rb"/Type\s*/Page\b",data)))
        if pages > 20: raise ValidationError(message="回单 PDF 页数超过 20 页限制")
        object_key=f"bank-receipts/{datetime.now():%Y/%m}/{uuid.uuid4().hex}.pdf"
        client=get_minio_client(); ensure_bucket_exists(client,settings.MINIO_BUCKET_CONTRACTS); client.put_object(settings.MINIO_BUCKET_CONTRACTS,object_key,BytesIO(data),len(data),content_type="application/pdf")
        batch = BankReceiptBatch(batch_number=f"BR-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:8]}", original_filename=upload.filename, uploaded_by=user.id)
        self.db.add(batch); await self.db.flush()
        item = BankReceiptItem(batch_id=batch.id, source_filename=upload.filename, sha256=digest, file_path=object_key, file_key=object_key, status="needs_review")
        try:
            self.db.add(item); await create_audit_log(self.db, user, "UPLOAD", "银行回单", description=upload.filename); await self.db.commit(); await self.db.refresh(batch); return batch
        except Exception:
            await self.db.rollback(); client.remove_object(settings.MINIO_BUCKET_CONTRACTS,object_key); raise
    async def process(self,batch_id:int):
        item=await self.db.scalar(select(BankReceiptItem).where(BankReceiptItem.batch_id==batch_id))
        batch=await self.db.get(BankReceiptBatch,batch_id)
        if not item or not batch:return
        item.status="processing"; batch.status="processing"; await self.db.commit()
        response=None
        try:
            config={x.key:x.value for x in (await self.db.execute(select(SystemConfig).where(SystemConfig.key.in_(["mineru_enabled","mineru_api_url","mineru_api_key","mineru_timeout_seconds","company_bank_accounts"])))).scalars()}
            client=get_minio_client(); obj=client.get_object(settings.MINIO_BUCKET_CONTRACTS,item.file_key)
            try:data=obj.read()
            finally:obj.close();obj.release_conn()
            try:text="\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages).strip()
            except Exception:text=""
            if len(text)<40:
                if str(config.get("mineru_enabled","")).lower()!="true": raise ValidationError(message="PDF 无可用文本层且 MinerU 未启用")
                if not config.get("mineru_api_url") or not config.get("mineru_api_key"): raise ValidationError(message="PDF 无可用文本层且 MinerU 配置缺失")
                from app.routers.system import _reveal_secret, _validate_external_api_url
                _validate_external_api_url(config["mineru_api_url"])
                async with httpx.AsyncClient(timeout=int(config.get("mineru_timeout_seconds") or 60)) as http:
                    response=await http.post(config["mineru_api_url"],headers={"Authorization":f"Bearer {_reveal_secret(config['mineru_api_key'])}"},files={"file":(item.source_filename,data,"application/pdf")})
                response.raise_for_status(); payload=response.json(); text=payload.get("text") or payload.get("markdown") or payload.get("content") or ""
            else:payload={"source":"pdf_text_layer","text":text}
            parsed=parse_receipt_text(text); accounts={x.strip() for x in (config.get("company_bank_accounts") or "").split(",") if x.strip()}
            for key,value in parsed.items():
                if hasattr(item,key):setattr(item,key,value)
            item.raw_mineru_result=payload; item.parsed_payload={**parsed,"text":text}; item.direction=determine_direction(accounts,item.payer_account,item.payee_account); item.status="needs_review"; item.error_message=None if parsed["amount_consistent"] else "中文大写金额与数字金额不一致，请人工复核"; batch.status="completed"
            counterparty=item.payer_name if item.direction=="receipt" else item.payee_name
            if item.direction in {"receipt","payment"} and counterparty:
                for result in await self.search(counterparty,item.direction):
                    self.db.add(BankReceiptMatchCandidate(item_id=item.id,direction=item.direction,contract_type=result["contract_type"],contract_id=result["id"],contract_name=result["contract_name"],score=80,matched_signals={"counterparty":counterparty}))
        except Exception as exc:
            item.status="failed"; item.error_message="MinerU 识别失败" if response is not None else str(exc); batch.status="failed"
        await self.db.commit()
    async def retry(self,item_id,user):
        item=await self.db.get(BankReceiptItem,item_id)
        if not item: raise ResourceNotFoundError(resource_type="银行回单",resource_id=item_id)
        if item.status!="failed": raise ValidationError(message="只有识别失败的回单可以重试")
        item.status="uploaded";item.error_message=None
        batch=await self.db.get(BankReceiptBatch,item.batch_id);batch.status="uploaded"
        await create_audit_log(self.db,user,"UPDATE","银行回单",item.id,description="重新识别",new_values={"status":"uploaded"});await self.db.commit();return item.batch_id
    async def batches(self): return list((await self.db.execute(select(BankReceiptBatch).order_by(BankReceiptBatch.created_at.desc()))).scalars())
    async def items(self, batch_id):
        return list((await self.db.execute(select(BankReceiptItem).options(selectinload(BankReceiptItem.allocations),selectinload(BankReceiptItem.candidates)).where(BankReceiptItem.batch_id == batch_id))).scalars())
    async def allocate(self, item_id, payload):
        item = await self.db.scalar(select(BankReceiptItem).where(BankReceiptItem.id == item_id).with_for_update())
        if not item: raise ResourceNotFoundError(resource_type="银行回单", resource_id=item_id)
        if item.status in {"confirmed", "processing", "ignored"}: raise ValidationError(message="当前状态不能修改分摊")
        if item.direction not in {"unknown", payload.direction}:
            raise ValidationError(message="分摊方向必须与已复核的回单方向一致")
        allocation = BankReceiptAllocation(item_id=item_id, **payload.model_dump())
        self.db.add(allocation); item.status = "ready"; await self.db.commit(); await self.db.refresh(allocation); return allocation
    async def review(self,item_id,payload,user):
        item=await self.db.scalar(select(BankReceiptItem).where(BankReceiptItem.id==item_id).with_for_update())
        if not item: raise ResourceNotFoundError(resource_type="银行回单",resource_id=item_id)
        if item.status in {"processing","confirmed","ignored"}: raise ValidationError(message="当前状态不能复核")
        for key,value in payload.model_dump().items(): setattr(item,key,value)
        item.status="ready" if await self.db.scalar(select(BankReceiptAllocation.id).where(BankReceiptAllocation.item_id==item_id).limit(1)) else "needs_review"
        await create_audit_log(self.db,user,"UPDATE","银行回单",item.id,new_values=payload.model_dump()); await self.db.commit(); return item
    async def confirm(self, item_id, user):
        item = (await self.db.execute(select(BankReceiptItem).options(selectinload(BankReceiptItem.allocations)).where(BankReceiptItem.id == item_id).with_for_update())).scalar_one_or_none()
        if not item: raise ResourceNotFoundError(resource_type="银行回单", resource_id=item_id)
        if item.status == "confirmed": return item
        if item.direction not in {"receipt", "payment"} or item.transaction_at is None: raise ValidationError(message="请先复核回单方向和交易时间")
        drafts = [a for a in item.allocations if a.status == "draft"]
        validate_receipt_allocation_total(item.amount, [a.amount for a in drafts])
        for allocation in drafts:
            common = dict(amount=allocation.amount, description=item.summary, file_path=item.file_path, file_key=item.file_key, storage_provider="minio" if item.file_key else "local", source_bank_receipt_item_id=item.id, source_bank_receipt_allocation_id=allocation.id, bank_serial_number=item.bank_serial_number, transaction_at=item.transaction_at, created_by=user.id, updated_by=user.id)
            if item.direction == "receipt":
                formal = FinanceUpstreamReceipt(contract_id=allocation.upstream_contract_id, receipt_date=item.transaction_at.date(), payer_name=item.payer_name, payer_account=item.payer_account, **common)
            elif allocation.downstream_contract_id:
                formal = FinanceDownstreamPayment(contract_id=allocation.downstream_contract_id, payment_date=item.transaction_at.date(), payee_name=item.payee_name, payee_account=item.payee_account, **common)
            else:
                formal = FinanceManagementPayment(contract_id=allocation.management_contract_id, payment_date=item.transaction_at.date(), payee_name=item.payee_name, payee_account=item.payee_account, **common)
            self.db.add(formal); await self.db.flush(); allocation.formal_record_id = formal.id; allocation.status = "confirmed"; allocation.confirmed_by = user.id; allocation.confirmed_at = datetime.utcnow()
        item.status = "confirmed"; await create_audit_log(self.db, user, "APPROVE", "银行回单", item.id, old_values=None, new_values={"allocations": [str(a.amount) for a in drafts]}); await self.db.commit(); return item
    async def clear(self, item_id, reason, user):
        item = (await self.db.execute(select(BankReceiptItem).options(selectinload(BankReceiptItem.allocations)).where(BankReceiptItem.id == item_id).with_for_update())).scalar_one_or_none()
        if not item: raise ResourceNotFoundError(resource_type="银行回单", resource_id=item_id)
        if item.status == "cleared": return item
        if item.status != "confirmed": raise ValidationError(message="只有已入账回单可以清除")
        snapshot = []
        for a in item.allocations:
            snapshot.append({"allocation_id": a.id, "formal_record_id": a.formal_record_id, "amount": str(a.amount)})
            table = FinanceUpstreamReceipt if item.direction == "receipt" else (FinanceDownstreamPayment if a.downstream_contract_id else FinanceManagementPayment)
            if a.formal_record_id:
                formal=await self.db.get(table,a.formal_record_id)
                if formal:
                    formal.original_amount=formal.amount; formal.amount=0; formal.posting_status="cleared"; formal.cleared_at=datetime.utcnow(); formal.clear_reason=reason
            a.status = "cleared"
        item.status = "cleared"; item.clear_reason = reason; item.cleared_by = user.id; item.cleared_at = datetime.utcnow()
        await create_audit_log(self.db, user, "DELETE", "银行回单入账", item.id, description=reason, old_values={"records": snapshot}); await self.db.commit(); return item
    async def search(self, q, direction):
        escaped=q.replace("\\","\\\\").replace("%","\\%").replace("_","\\_"); pattern = f"%{escaped}%"; results=[]
        models = [("upstream", ContractUpstream)] if direction == "receipt" else [("downstream", ContractDownstream), ("management", ContractManagement)]
        for kind, model in models:
            rows=(await self.db.execute(select(model).where(model.contract_name.ilike(pattern,escape="\\")).order_by(func.length(model.contract_name)).limit(20))).scalars()
            results += [{"contract_type": kind, "id": x.id, "serial_number":x.serial_number,"contract_name": x.contract_name, "contract_code": x.contract_code,"counterparty":x.party_a_name if kind=="upstream" else x.party_b_name,"remaining_amount":str(x.contract_amount or 0)} for x in rows]
        return results[:20]
    async def ignore(self,item_id,reason,user):
        item=await self.db.get(BankReceiptItem,item_id)
        if not item: raise ResourceNotFoundError(resource_type="银行回单",resource_id=item_id)
        if item.status not in {"needs_review","ready","cleared"}: raise ValidationError(message="当前状态不能忽略")
        item.status="ignored"; item.clear_reason=reason; await create_audit_log(self.db,user,"UPDATE","银行回单",item.id,description=reason,new_values={"status":"ignored"}); await self.db.commit(); return item
    async def delete_failed(self,item_id,user):
        item=await self.db.get(BankReceiptItem,item_id)
        if not item: raise ResourceNotFoundError(resource_type="银行回单",resource_id=item_id)
        if item.status!="failed" or await self.db.scalar(select(BankReceiptAllocation.formal_record_id).where(BankReceiptAllocation.item_id==item_id,BankReceiptAllocation.formal_record_id.is_not(None))): raise ValidationError(message="只有未入账的失败回单可以删除")
        key=item.file_key
        if key:
            try:get_minio_client().remove_object(settings.MINIO_BUCKET_CONTRACTS,key)
            except Exception as exc:
                item.error_message=f"源文件删除失败，可重试：{type(exc).__name__}";await self.db.commit();raise ValidationError(message="源文件删除失败，数据库记录已保留，请重试")
        await self.db.delete(item); await create_audit_log(self.db,user,"DELETE","银行回单失败文件",item_id); await self.db.commit()
