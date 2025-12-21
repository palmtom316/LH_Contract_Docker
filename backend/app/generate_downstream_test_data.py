"""
生成下游合同测试数据
- 10条下游合同记录（2025/12/1-2025/12/31）
- 每个合同关联上游合同
- 每个合同添加1-3条应付款、挂账、付款、结算数据
"""
import asyncio
import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import random

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import (
    ContractDownstream,
    FinanceDownstreamPayable,
    FinanceDownstreamInvoice,
    FinanceDownstreamPayment,
    DownstreamSettlement
)
from app.models.system import SysDictionary

# 测试数据配置
PARTY_A_NAME = "蓝海电力工程有限公司"

PARTY_B_NAMES = [
    "江苏电力施工有限公司",
    "华能电力工程公司",
    "南方电力设备有限公司",
    "中建电力集团",
    "天辰电力科技",
    "华电工程有限公司",
    "国电建设集团",
    "远东电力公司",
    "中电装备集团",
    "华通电力工程"
]

CONTRACT_NAMES = [
    "变电站土建工程分包",
    "电气设备安装工程",
    "输电线路施工",
    "配电设备采购",
    "自动化系统集成",
    "电缆敷设工程",
    "变压器安装调试",
    "配电柜制造安装",
    "线路迁改施工",
    "设备运维服务"
]

RESPONSIBLE_PERSONS = ["张伟", "李明", "王强", "刘洋", "陈杰", "赵磊", "孙涛", "周建", "吴勇", "郑鹏"]

async def get_dict_options(db, category):
    """获取数据字典选项"""
    result = await db.execute(
        select(SysDictionary)
        .where(SysDictionary.category == category)
        .where(SysDictionary.is_active == True)
    )
    options = result.scalars().all()
    return [opt.value for opt in options] if options else []

async def generate_downstream_contracts():
    """生成下游合同测试数据"""
    async with AsyncSessionLocal() as db:
        try:
            print("=" * 60)
            print("开始生成下游合同测试数据...")
            print("=" * 60)
            
            # 获取所有上游合同
            result = await db.execute(
                select(ContractUpstream).order_by(ContractUpstream.id)
            )
            upstream_contracts = result.scalars().all()
            
            if not upstream_contracts:
                print("错误: 没有找到上游合同，请先运行 generate_upstream_test_data.py")
                return
            
            print(f"\n找到 {len(upstream_contracts)} 条上游合同")
            
            # 获取数据字典选项
            categories = await get_dict_options(db, "downstream_contract_category")
            pricing_modes = await get_dict_options(db, "downstream_pricing_mode")
            payment_categories = await get_dict_options(db, "payment_category")
            
            # 如果没有数据字典，使用默认值
            if not categories:
                categories = ["专业分包", "劳务分包", "设备采购", "材料采购", "技术服务"]
            if not pricing_modes:
                pricing_modes = ["固定总价", "单价合同", "成本加酬金"]
            if not payment_categories:
                payment_categories = ["预付款", "进度款", "结算款", "质保金"]
            
            print(f"\n数据字典选项:")
            print(f"  合同类别: {categories}")
            print(f"  计价模式: {pricing_modes}")
            print(f"  应付款类别: {payment_categories}")
            
            # 日期范围：2025/12/1 - 2025/12/31
            start_date = date(2025, 12, 1)
            end_date = date(2025, 12, 31)
            
            created_contracts = []
            
            # 生成10条下游合同，每条关联一个上游合同
            for i in range(1, 11):
                # 选择对应的上游合同
                upstream_contract = upstream_contracts[i-1]
                
                # 随机生成合同日期
                days_offset = random.randint(0, 15)
                sign_date = start_date + timedelta(days=days_offset)
                contract_start = sign_date + timedelta(days=random.randint(1, 5))
                contract_end = end_date
                
                # 生成合同金额（上游合同金额的40%-70%）
                contract_amount = upstream_contract.contract_amount * Decimal(random.uniform(0.4, 0.7))
                
                contract = ContractDownstream(
                    contract_code=f"XY-2025-{i:04d}",
                    contract_name=CONTRACT_NAMES[i-1],
                    party_a_name=PARTY_A_NAME,
                    party_b_name=PARTY_B_NAMES[i-1],
                    upstream_contract_id=upstream_contract.id,
                    category=random.choice(categories),
                    pricing_mode=random.choice(pricing_modes),
                    responsible_person=random.choice(RESPONSIBLE_PERSONS),
                    party_a_contact=random.choice(RESPONSIBLE_PERSONS),
                    party_a_phone=f"138{random.randint(10000000, 99999999)}",
                    party_b_contact=f"{PARTY_B_NAMES[i-1][:2]}经理",
                    party_b_phone=f"139{random.randint(10000000, 99999999)}",
                    contract_amount=contract_amount,
                    sign_date=sign_date,
                    start_date=contract_start,
                    end_date=contract_end,
                    status="执行中",
                    notes=f"测试数据 - 下游合同{i}"
                )
                
                db.add(contract)
                await db.flush()
                
                print(f"\n创建下游合同 {i}/10:")
                print(f"  合同编号: {contract.contract_code}")
                print(f"  合同名称: {contract.contract_name}")
                print(f"  乙方: {contract.party_b_name}")
                print(f"  关联上游: {upstream_contract.contract_code} - {upstream_contract.contract_name}")
                print(f"  合同金额: ¥{contract_amount:,.2f}")
                print(f"  签订日期: {sign_date}")
                
                # 为每个合同添加应付款（1-3条）
                payable_count = random.randint(1, 3)
                print(f"  添加应付款 {payable_count} 条:")
                
                total_payable = Decimal(0)
                for j in range(payable_count):
                    payable_amount = contract_amount * Decimal(random.uniform(0.15, 0.35))
                    expected_date = sign_date + timedelta(days=random.randint(1, 25))
                    
                    payable = FinanceDownstreamPayable(
                        contract_id=contract.id,
                        category=random.choice(payment_categories),
                        amount=payable_amount,
                        description=f"测试应付款-{j+1}",
                        expected_date=expected_date
                    )
                    db.add(payable)
                    total_payable += payable_amount
                    print(f"    {j+1}. {payable.category}: ¥{payable_amount:,.2f} (预计:{expected_date})")
                
                # 为每个合同添加收票/挂账（1-3条）
                invoice_count = random.randint(1, 3)
                print(f"  添加收票 {invoice_count} 条:")
                
                total_invoiced = Decimal(0)
                for j in range(invoice_count):
                    invoice_amount = contract_amount * Decimal(random.uniform(0.10, 0.30))
                    invoice_date = sign_date + timedelta(days=random.randint(5, 28))
                    
                    invoice = FinanceDownstreamInvoice(
                        contract_id=contract.id,
                        invoice_number=f"DINV-2025-{i:04d}-{j+1:02d}",
                        invoice_date=invoice_date,
                        amount=invoice_amount,
                        tax_rate=Decimal("13.00"),
                        tax_amount=invoice_amount * Decimal("0.13"),
                        invoice_type="增值税专用发票",
                        supplier_name=contract.party_b_name,
                        description=f"测试收票-{j+1}"
                    )
                    db.add(invoice)
                    total_invoiced += invoice_amount
                    print(f"    {j+1}. {invoice.invoice_number}: ¥{invoice_amount:,.2f} (日期:{invoice_date})")
                
                # 为每个合同添加付款（1-3条）
                payment_count = random.randint(1, 3)
                print(f"  添加付款 {payment_count} 条:")
                
                total_paid = Decimal(0)
                for j in range(payment_count):
                    payment_amount = contract_amount * Decimal(random.uniform(0.08, 0.25))
                    payment_date = sign_date + timedelta(days=random.randint(10, 30))
                    
                    payment = FinanceDownstreamPayment(
                        contract_id=contract.id,
                        payment_date=payment_date,
                        amount=payment_amount,
                        payment_method="银行转账",
                        payee_name=contract.party_b_name,
                        payee_account=f"6228{random.randint(1000000000000, 9999999999999)}",
                        payee_bank="中国建设银行",
                        description=f"测试付款-{j+1}"
                    )
                    db.add(payment)
                    total_paid += payment_amount
                    print(f"    {j+1}. ¥{payment_amount:,.2f} (日期:{payment_date})")
                
                # 为每个合同添加结算（1-2条）
                settlement_count = random.randint(1, 2)
                print(f"  添加结算 {settlement_count} 条:")
                
                total_settlement = Decimal(0)
                for j in range(settlement_count):
                    settlement_amount = contract_amount * Decimal(random.uniform(0.20, 0.45))
                    settlement_date = sign_date + timedelta(days=random.randint(15, 30))
                    completion_date = sign_date + timedelta(days=random.randint(20, 29))
                    
                    settlement = DownstreamSettlement(
                        contract_id=contract.id,
                        settlement_code=f"DJS-2025-{i:04d}-{j+1:02d}",
                        settlement_date=settlement_date,
                        completion_date=completion_date,
                        settlement_amount=settlement_amount,
                        audit_amount=settlement_amount * Decimal("0.98"),
                        final_amount=settlement_amount * Decimal("0.97"),
                        status="已审核",
                        description=f"测试结算-{j+1}"
                    )
                    db.add(settlement)
                    total_settlement += settlement_amount
                    print(f"    {j+1}. {settlement.settlement_code}: ¥{settlement_amount:,.2f}")
                
                print(f"  统计:")
                print(f"    总应付: ¥{total_payable:,.2f}")
                print(f"    总收票: ¥{total_invoiced:,.2f}")
                print(f"    总付款: ¥{total_paid:,.2f}")
                print(f"    总结算: ¥{total_settlement:,.2f}")
                
                created_contracts.append(contract)
            
            # 提交所有数据
            await db.commit()
            
            print("\n" + "=" * 60)
            print("✓ 下游合同测试数据生成完成！")
            print(f"  总共生成: {len(created_contracts)} 条下游合同")
            print("=" * 60)
            
            return created_contracts
            
        except Exception as e:
            await db.rollback()
            print(f"\n✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    asyncio.run(generate_downstream_contracts())
