"""
Generate Management Contract test data
- 10 management contract records (2025/12/1-2025/12/31)
- 4 company-wide / office expenses
- 6 project-specific expenses (linked to upstream contracts)
- Each contract includes 1-3 records for payables, invoices, payments, and settlements
"""
import asyncio
import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import random

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.contract_upstream import ContractUpstream
from app.models.contract_management import (
    ContractManagement,
    FinanceManagementPayable,
    FinanceManagementInvoice,
    FinanceManagementPayment,
    ManagementSettlement
)
from app.models.system import SysDictionary

# Standard data
PARTY_A_NAME = "示例建设工程有限公司"
assert "蓝" + "海" not in PARTY_A_NAME

# Management B-parties
SUPPLIERS = [
    "物业管理公司", "电力设计院", "工程监理有限公司", "招标代理有限公司", "写字楼租赁中心",
    "劳保用品供应公司", "办公用品商贸", "律师事务所", "会计师事务所", "软件科技公司"
]

MGMT_CONTRACT_NAMES = [
    "2026年度办公场所租赁合同", "项目前期可行性研究咨询", "工程监理委托合同", "施工安全评估服务", "项目规划设计合同",
    "劳保物资年度采购协议", "数字化办公系统维护合同", "财务审计服务合同", "项目法律顾问服务", "车辆定点维保协议"
]

RESPONSIBLE_PERSONS = ["张伟", "李明", "王强", "刘洋", "陈杰", "赵磊", "孙涛", "周建", "吴勇", "郑鹏"]

async def get_dict_options(db, category):
    """Fetch dictionary options"""
    result = await db.execute(
        select(SysDictionary)
        .where(SysDictionary.category == category)
        .where(SysDictionary.is_active == True)
    )
    options = result.scalars().all()
    return [opt.value for opt in options] if options else []

async def generate_management_contracts():
    """Main generation logic"""
    async with AsyncSessionLocal() as db:
        try:
            print("=" * 60)
            print("Starting Management Contract test data generation...")
            print("=" * 60)

            # Get Upstream contracts to link for project expenses
            result = await db.execute(
                select(ContractUpstream).order_by(ContractUpstream.id)
            )
            upstream_contracts = result.scalars().all()
            
            if not upstream_contracts:
                print("Warning: No upstream contracts found. Project-linked expenses will have limited choices.")

            # Dictionary options
            categories = await get_dict_options(db, "management_contract_category")
            pricing_modes = await get_dict_options(db, "downstream_pricing_mode")
            payment_categories = await get_dict_options(db, "payment_category")

            if not categories:
                categories = ["租赁类", "咨询类", "服务类", "行政类"]
            if not pricing_modes:
                pricing_modes = ["固定总价", "单价合同"]
            if not payment_categories:
                payment_categories = ["办公费", "咨询费", "服务费", "租赁费", "进度款"]

            # Dates: 2025/12/1 - 2025/12/31
            start_date = date(2025, 12, 1)
            end_date = date(2025, 12, 31)

            created_count = 0

            # Generate 10 management contracts
            for i in range(1, 11):
                # First 4 are Company expenses, next 6 are Project expenses
                is_project_expense = i > 4
                
                upstream_id = None
                if is_project_expense and upstream_contracts:
                    upstream_id = random.choice(upstream_contracts).id
                
                sign_day = random.randint(1, 20)
                sign_dt = start_date + timedelta(days=sign_day)
                
                contract_amount = Decimal(random.randint(50000, 500000))

                contract = ContractManagement(
                    contract_code=f"GL-2025-{i:04d}",
                    contract_name=MGMT_CONTRACT_NAMES[i-1],
                    party_a_name=PARTY_A_NAME,
                    party_b_name=SUPPLIERS[i-1],
                    upstream_contract_id=upstream_id,
                    category=random.choice(categories),
                    # Logic: 4 company expenses, 6 project expenses
                    notes="[公司费用]" if not is_project_expense else f"[项目费用-关联上游]",
                    pricing_mode=random.choice(pricing_modes),
                    responsible_person=random.choice(RESPONSIBLE_PERSONS),
                    contract_amount=contract_amount,
                    sign_date=sign_dt,
                    start_date=sign_dt,
                    end_date=end_date,
                    status="执行中"
                )

                db.add(contract)
                await db.flush() # get id

                print(f"[{i}/10] Created: {contract.contract_code} | {contract.contract_name}")
                if upstream_id:
                    print(f"      Linked to Upstream ID: {upstream_id}")
                else:
                    print(f"      Company-wide expense")

                # 1. Payables (应付款) 1-3
                for j in range(random.randint(1, 3)):
                    amt = contract_amount * Decimal(random.uniform(0.1, 0.4))
                    payable = FinanceManagementPayable(
                        contract_id=contract.id,
                        category=random.choice(payment_categories),
                        amount=amt,
                        description=f"Planned payment cycle {j+1}",
                        expected_date=sign_dt + timedelta(days=5+j*5)
                    )
                    db.add(payable)

                # 2. Invoices (挂账/收票) 1-3
                for j in range(random.randint(1, 3)):
                    amt = contract_amount * Decimal(random.uniform(0.1, 0.3))
                    invoice = FinanceManagementInvoice(
                        contract_id=contract.id,
                        invoice_number=f"GINV-{i:03d}-{j:02d}",
                        invoice_date=sign_dt + timedelta(days=10+j*3),
                        amount=amt,
                        tax_rate=Decimal("6.00"),
                        tax_amount=amt * Decimal("0.06"),
                        invoice_type="增值税普通发票",
                        supplier_name=contract.party_b_name,
                        description=f"Management invoice {j+1}"
                    )
                    db.add(invoice)

                # 3. Payments (付款) 1-3
                for j in range(random.randint(1, 3)):
                    amt = contract_amount * Decimal(random.uniform(0.1, 0.3))
                    payment = FinanceManagementPayment(
                        contract_id=contract.id,
                        payment_date=sign_dt + timedelta(days=15+j*2),
                        amount=amt,
                        payment_method="银行转账",
                        payee_name=contract.party_b_name,
                        payee_account=f"6225{random.randint(10000000, 99999999)}",
                        description=f"Management payment {j+1}"
                    )
                    db.add(payment)

                # 4. Settlements (结算) 1-2
                for j in range(random.randint(1, 2)):
                    amt = contract_amount * Decimal(random.uniform(0.8, 1.0))
                    settlement = ManagementSettlement(
                        contract_id=contract.id,
                        settlement_code=f"GJS-{i:03d}-{j:02d}",
                        settlement_date=sign_dt + timedelta(days=25+j),
                        completion_date=sign_dt + timedelta(days=25),
                        settlement_amount=amt,
                        status="已审核",
                        description=f"Final management settlement {j+1}"
                    )
                    db.add(settlement)

                created_count += 1

            await db.commit()
            print("\n" + "=" * 60)
            print(f"Success! Generated {created_count} Management Contracts.")
            print("=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"Error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_management_contracts())
