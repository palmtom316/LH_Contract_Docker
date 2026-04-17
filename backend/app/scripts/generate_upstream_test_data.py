"""
生成上游合同测试数据
- 10条上游合同记录（2025/12/1-2025/12/31）
- 每个合同添加1-3条应收款、挂账、回款、结算数据
"""
import asyncio
import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import random

# Add backend/ root to Python path (file lives at backend/app/scripts/*.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.contract_upstream import (
    ContractUpstream, 
    FinanceUpstreamReceivable,
    FinanceUpstreamInvoice,
    FinanceUpstreamReceipt,
    ProjectSettlement
)
from app.models.system import SysDictionary

# 测试数据配置
PARTY_A_NAMES = [
    "国网江苏省电力有限公司",
    "南方电网广东电网公司",
    "华能国际电力股份有限公司",
    "大唐电力集团",
    "国家电投集团",
    "华电集团有限公司",
    "中国电建集团",
    "中国能建集团",
    "国网浙江省电力有限公司",
    "国网山东省电力公司"
]

PARTY_B_NAME = "示例机电工程有限公司"
assert "蓝" + "海" not in PARTY_B_NAME

PROJECT_NAMES = [
    "220kV变电站新建工程",
    "城市配电网改造项目",
    "智能电网升级改造工程",
    "风电场接入系统工程",
    "光伏电站并网工程",
    "输电线路迁改工程",
    "变电站扩建工程",
    "配电自动化项目",
    "电力物联网建设项目",
    "充电桩基础设施工程"
]

PROJECT_LOCATIONS = [
    "江苏省南京市",
    "广东省广州市",
    "浙江省杭州市",
    "山东省济南市",
    "上海市浦东新区",
    "北京市朝阳区",
    "四川省成都市",
    "湖北省武汉市",
    "安徽省合肥市",
    "河南省郑州市"
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

async def generate_upstream_contracts():
    """生成上游合同测试数据"""
    async with AsyncSessionLocal() as db:
        try:
            print("=" * 60)
            print("开始生成上游合同测试数据...")
            print("=" * 60)
            
            # 获取数据字典选项
            categories = await get_dict_options(db, "contract_category")
            project_categories = await get_dict_options(db, "project_category")
            pricing_modes = await get_dict_options(db, "pricing_mode")
            management_modes = await get_dict_options(db, "management_mode")
            receivable_categories = await get_dict_options(db, "receivable_category")
            
            # 如果没有数据字典，使用默认值
            if not categories:
                categories = ["工程总包", "专业分包", "设备采购", "技术服务"]
            if not project_categories:
                project_categories = ["示例总公司", "示例子公司一", "示例子公司二"]
            if not pricing_modes:
                pricing_modes = ["固定总价", "单价合同", "成本加酬金"]
            if not management_modes:
                management_modes = ["自营", "联营", "挂靠"]
            if not receivable_categories:
                receivable_categories = ["预付款", "进度款", "结算款", "质保金"]
            
            print(f"\n数据字典选项:")
            print(f"  合同类别: {categories}")
            print(f"  公司分类: {project_categories}")
            print(f"  计价模式: {pricing_modes}")
            print(f"  管理模式: {management_modes}")
            print(f"  应收款类别: {receivable_categories}")
            
            # 日期范围：2025/12/1 - 2025/12/31
            start_date = date(2025, 12, 1)
            end_date = date(2025, 12, 31)
            
            created_contracts = []
            
            # 生成10条上游合同
            for i in range(1, 11):
                # 随机生成合同日期
                days_offset = random.randint(0, 15)
                sign_date = start_date + timedelta(days=days_offset)
                contract_start = sign_date + timedelta(days=random.randint(1, 5))
                contract_end = end_date
                
                # 生成合同金额（100万-2000万）
                contract_amount = Decimal(random.randint(1000000, 20000000))
                
                contract = ContractUpstream(
                    contract_code=f"SH-2025-{i:04d}",
                    contract_name=f"{PROJECT_NAMES[i-1]}",
                    party_a_name=PARTY_A_NAMES[i-1],
                    party_b_name=PARTY_B_NAME,
                    category=random.choice(categories),
                    company_category=random.choice(project_categories),
                    pricing_mode=random.choice(pricing_modes),
                    management_mode=random.choice(management_modes),
                    responsible_person=random.choice(RESPONSIBLE_PERSONS),
                    party_a_contact=f"{RESPONSIBLE_PERSONS[i-1]}",
                    party_a_phone=f"138{random.randint(10000000, 99999999)}",
                    project_name=PROJECT_NAMES[i-1],
                    project_location=PROJECT_LOCATIONS[i-1],
                    contract_amount=contract_amount,
                    sign_date=sign_date,
                    start_date=contract_start,
                    end_date=contract_end,
                    status="执行中",
                    notes=f"测试数据 - 上游合同{i}"
                )
                
                db.add(contract)
                await db.flush()  # 获取contract.id
                
                print(f"\n创建上游合同 {i}/10:")
                print(f"  合同编号: {contract.contract_code}")
                print(f"  合同名称: {contract.contract_name}")
                print(f"  甲方: {contract.party_a_name}")
                print(f"  合同金额: ¥{contract_amount:,.2f}")
                print(f"  签订日期: {sign_date}")
                
                # 为每个合同添加应收款（1-3条）
                receivable_count = random.randint(1, 3)
                print(f"  添加应收款 {receivable_count} 条:")
                
                total_receivable = Decimal(0)
                for j in range(receivable_count):
                    receivable_amount = contract_amount * Decimal(random.uniform(0.15, 0.35))
                    receivable_date = sign_date + timedelta(days=random.randint(1, 25))
                    
                    receivable = FinanceUpstreamReceivable(
                        contract_id=contract.id,
                        category=random.choice(receivable_categories),
                        amount=receivable_amount,
                        description=f"测试应收款-{j+1}",
                        expected_date=receivable_date
                    )
                    db.add(receivable)
                    total_receivable += receivable_amount
                    print(f"    {j+1}. {receivable.category}: ¥{receivable_amount:,.2f} (预计:{receivable_date})")
                
                # 为每个合同添加挂账/开票（1-3条）
                invoice_count = random.randint(1, 3)
                print(f"  添加挂账 {invoice_count} 条:")
                
                total_invoiced = Decimal(0)
                for j in range(invoice_count):
                    invoice_amount = contract_amount * Decimal(random.uniform(0.10, 0.30))
                    invoice_date = sign_date + timedelta(days=random.randint(5, 28))
                    
                    invoice = FinanceUpstreamInvoice(
                        contract_id=contract.id,
                        invoice_number=f"INV-2025-{i:04d}-{j+1:02d}",
                        invoice_date=invoice_date,
                        amount=invoice_amount,
                        tax_rate=Decimal("13.00"),
                        tax_amount=invoice_amount * Decimal("0.13"),
                        invoice_type="增值税专用发票",
                        description=f"测试开票-{j+1}"
                    )
                    db.add(invoice)
                    total_invoiced += invoice_amount
                    print(f"    {j+1}. {invoice.invoice_number}: ¥{invoice_amount:,.2f} (日期:{invoice_date})")
                
                # 为每个合同添加回款（1-3条）
                receipt_count = random.randint(1, 3)
                print(f"  添加回款 {receipt_count} 条:")
                
                total_received = Decimal(0)
                for j in range(receipt_count):
                    receipt_amount = contract_amount * Decimal(random.uniform(0.08, 0.25))
                    receipt_date = sign_date + timedelta(days=random.randint(10, 30))
                    
                    receipt = FinanceUpstreamReceipt(
                        contract_id=contract.id,
                        receipt_date=receipt_date,
                        amount=receipt_amount,
                        payment_method="银行转账",
                        payer_name=contract.party_a_name,
                        payer_account=f"6222{random.randint(1000000000000, 9999999999999)}",
                        description=f"测试回款-{j+1}"
                    )
                    db.add(receipt)
                    total_received += receipt_amount
                    print(f"    {j+1}. ¥{receipt_amount:,.2f} (日期:{receipt_date})")
                
                # 为每个合同添加结算（1-2条）
                settlement_count = random.randint(1, 2)
                print(f"  添加结算 {settlement_count} 条:")
                
                total_settlement = Decimal(0)
                for j in range(settlement_count):
                    settlement_amount = contract_amount * Decimal(random.uniform(0.20, 0.45))
                    settlement_date = sign_date + timedelta(days=random.randint(15, 30))
                    completion_date = sign_date + timedelta(days=random.randint(20, 29))
                    
                    settlement = ProjectSettlement(
                        contract_id=contract.id,
                        settlement_code=f"JS-2025-{i:04d}-{j+1:02d}",
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
                print(f"    总应收: ¥{total_receivable:,.2f}")
                print(f"    总挂账: ¥{total_invoiced:,.2f}")
                print(f"    总回款: ¥{total_received:,.2f}")
                print(f"    总结算: ¥{total_settlement:,.2f}")
                
                created_contracts.append(contract)
            
            # 提交所有数据
            await db.commit()
            
            print("\n" + "=" * 60)
            print("✓ 上游合同测试数据生成完成！")
            print(f"  总共生成: {len(created_contracts)} 条上游合同")
            print("=" * 60)
            
            return created_contracts
            
        except Exception as e:
            await db.rollback()
            print(f"\n✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    asyncio.run(generate_upstream_contracts())
