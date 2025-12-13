"""
Test Data Population Script for LH Contract Management System
Generates realistic test data for all contract types and related financial records.
"""
import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal
import sys
sys.path.insert(0, '/Users/palmtom/LH_Contract_Docker/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql+asyncpg://lh_admin:LanHai2024Secure!@localhost:5432/lh_contract_db"

# Enum values (using Name keys as stored in DB)
UPSTREAM_CATEGORIES = ['GENERAL', 'SUB_PRO', 'SUB_LABOR', 'SERVICE', 'MAINTENANCE', 'MATERIAL', 'OTHER']
DOWNSTREAM_CATEGORIES = ['材料设备', '专业分包', '劳务分包', '咨询服务', '技术服务', '其他合同']
PRICING_MODES = ['FIXED_TOTAL', 'FIXED_UNIT', 'LABOR_UNIT', 'RATE_FLOAT']
MANAGEMENT_MODES = ['SELF', 'COOP', 'AFFILIATE']
RECEIVABLE_CATEGORIES = ['ADVANCE_PAYMENT', 'PROGRESS_PAYMENT', 'SETTLEMENT_PAYMENT', 'RETENTION_MONEY', 'OTHER']
PAYMENT_CATEGORIES = ['PREPAYMENT', 'PROGRESS', 'COMPLETION', 'SETTLEMENT', 'WARRANTY']
EXPENSE_CATEGORIES = ['COMPANY', 'PROJECT']
EXPENSE_TYPES = ['MANAGEMENT', 'TRAINING', 'CATERING', 'TRANSPORT', 'CONSULTING', 'BUSINESS', 'LEASING', 'QUALIFICATION', 'VEHICLE']
COMPANY_CATEGORIES = ['市区配网', '市北配网', '用户工程', '维护工程', '变电工程', '营销工程', '北源工程', '安驰工程']
CONTRACT_STATUSES = ['进行中', '已完成', '已终止']

# Sample data
PARTY_A_NAMES = [
    '重庆市电力公司', '国网重庆供电公司', '重庆能源集团', '重庆电网公司',
    '渝北区供电局', '江北区电力公司', '南岸区供电局', '九龙坡电力公司',
    '沙坪坝供电局', '渝中区电力公司'
]

PARTY_B_NAMES = [
    '重庆蓝海电气工程有限公司'
]

SUPPLIER_NAMES = [
    '重庆华电设备有限公司', '四川电力设备厂', '成都电气科技有限公司',
    '重庆宏达电力工程公司', '贵州电力设备股份公司', '云南电气工程有限公司',
    '重庆永川电力设备厂', '重庆万州电气公司', '重庆涪陵电力工程公司',
    '重庆合川电气设备厂'
]

PROJECT_NAMES = [
    '渝北区配电网改造工程', '江北区10kV线路新建工程', '南岸区变电站扩建项目',
    '九龙坡区电缆沟工程', '沙坪坝区智能电网建设', '渝中区老旧线路改造',
    '北碚区农网升级工程', '巴南区工业园区供电工程', '大渡口区配电房建设',
    '璧山区高压线路工程'
]

RESPONSIBLE_PERSONS = ['张伟', '李强', '王芳', '刘洋', '陈明', '杨军', '赵雷', '周涛', '吴刚', '郑浩']


def random_date_2025():
    """Generate a random date in 2025"""
    start = date(2025, 1, 1)
    end = date(2025, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def random_amount(min_val=100000, max_val=5000000):
    """Generate a random amount"""
    return Decimal(str(round(random.uniform(min_val, max_val), 2)))


def random_small_amount(min_val=10000, max_val=500000):
    """Generate a smaller random amount for financial records"""
    return Decimal(str(round(random.uniform(min_val, max_val), 2)))


async def populate_data():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # ========== 1. Upstream Contracts (10) ==========
            print("Creating 10 upstream contracts...")
            upstream_ids = []
            for i in range(1, 11):
                sign_date = random_date_2025()
                contract_amount = random_amount()
                
                sql = """
                INSERT INTO contracts_upstream 
                (serial_number, contract_code, contract_name, party_a_name, party_b_name, 
                 category, company_category, pricing_mode, management_mode, 
                 responsible_person, project_name, project_location, contract_amount, 
                 sign_date, start_date, end_date, status, notes, created_by)
                VALUES 
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                RETURNING id
                """
                result = await session.execute(
                    sql,
                    (
                        i,  # serial_number
                        f'LH-2025{str(i).zfill(2)}-{str(i).zfill(3)}',  # contract_code
                        f'{random.choice(PROJECT_NAMES)}（{i}期）',  # contract_name
                        random.choice(PARTY_A_NAMES),  # party_a_name
                        random.choice(PARTY_B_NAMES),  # party_b_name
                        random.choice(UPSTREAM_CATEGORIES),  # category
                        random.choice(COMPANY_CATEGORIES),  # company_category
                        random.choice(PRICING_MODES),  # pricing_mode
                        random.choice(MANAGEMENT_MODES),  # management_mode
                        random.choice(RESPONSIBLE_PERSONS),  # responsible_person
                        random.choice(PROJECT_NAMES),  # project_name
                        '重庆市' + random.choice(['渝北区', '江北区', '南岸区', '九龙坡区', '沙坪坝区']),  # location
                        contract_amount,  # contract_amount
                        sign_date,  # sign_date
                        sign_date + timedelta(days=random.randint(7, 30)),  # start_date
                        sign_date + timedelta(days=random.randint(180, 365)),  # end_date
                        random.choice(CONTRACT_STATUSES),  # status
                        f'上游合同测试数据{i}',  # notes
                        1  # created_by (admin)
                    )
                )
                
            # Use raw SQL for simplicity
            from sqlalchemy import text
            
            # Insert upstream contracts
            for i in range(1, 11):
                sign_date = random_date_2025()
                contract_amount = random_amount()
                
                await session.execute(text("""
                    INSERT INTO contracts_upstream 
                    (serial_number, contract_code, contract_name, party_a_name, party_b_name, 
                     category, company_category, pricing_mode, management_mode, 
                     responsible_person, project_name, project_location, contract_amount, 
                     sign_date, start_date, end_date, status, notes, created_by)
                    VALUES 
                    (:sn, :code, :name, :pa, :pb, :cat, :cc, :pm, :mm, :rp, :pn, :pl, :amt, :sd, :st, :ed, :stat, :notes, :cb)
                """), {
                    'sn': i,
                    'code': f'LH-2025{str(i).zfill(2)}-{str(i).zfill(3)}',
                    'name': f'{random.choice(PROJECT_NAMES)}（{i}期）',
                    'pa': random.choice(PARTY_A_NAMES),
                    'pb': random.choice(PARTY_B_NAMES),
                    'cat': random.choice(UPSTREAM_CATEGORIES),
                    'cc': random.choice(COMPANY_CATEGORIES),
                    'pm': random.choice(PRICING_MODES),
                    'mm': random.choice(MANAGEMENT_MODES),
                    'rp': random.choice(RESPONSIBLE_PERSONS),
                    'pn': random.choice(PROJECT_NAMES),
                    'pl': '重庆市' + random.choice(['渝北区', '江北区', '南岸区', '九龙坡区', '沙坪坝区']),
                    'amt': float(contract_amount),
                    'sd': sign_date,
                    'st': sign_date + timedelta(days=random.randint(7, 30)),
                    'ed': sign_date + timedelta(days=random.randint(180, 365)),
                    'stat': random.choice(CONTRACT_STATUSES),
                    'notes': f'上游合同测试数据{i}',
                    'cb': 1
                })
            
            await session.commit()
            
            # Get upstream IDs
            result = await session.execute(text("SELECT id FROM contracts_upstream ORDER BY id"))
            upstream_ids = [row[0] for row in result.fetchall()]
            print(f"  Created upstream contracts: {upstream_ids}")
            
            # ========== 2. Upstream Financial Records ==========
            print("Creating upstream financial records...")
            for uid in upstream_ids:
                # Receivables (1-3 records)
                for _ in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_upstream_receivables 
                        (contract_id, category, amount, description, expected_date, created_by)
                        VALUES (:cid, :cat, :amt, :desc, :dt, :cb)
                    """), {
                        'cid': uid,
                        'cat': random.choice(RECEIVABLE_CATEGORIES),
                        'amt': float(random_small_amount()),
                        'desc': f'应收款记录-合同{uid}',
                        'dt': random_date_2025(),
                        'cb': 1
                    })
                
                # Invoices (1-3 records)
                for j in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_upstream_invoices 
                        (contract_id, invoice_number, invoice_date, amount, description, created_by)
                        VALUES (:cid, :inv, :dt, :amt, :desc, :cb)
                    """), {
                        'cid': uid,
                        'inv': f'INV-2025-{uid:03d}-{j+1:02d}',
                        'dt': random_date_2025(),
                        'amt': float(random_small_amount()),
                        'desc': f'挂账记录-合同{uid}',
                        'cb': 1
                    })
                
                # Receipts (1-3 records)
                for _ in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_upstream_receipts 
                        (contract_id, receipt_date, amount, payment_method, payer_name, description, created_by)
                        VALUES (:cid, :dt, :amt, :pm, :pn, :desc, :cb)
                    """), {
                        'cid': uid,
                        'dt': random_date_2025(),
                        'amt': float(random_small_amount()),
                        'pm': random.choice(['银行转账', '支票', '电汇']),
                        'pn': random.choice(PARTY_A_NAMES),
                        'desc': f'回款记录-合同{uid}',
                        'cb': 1
                    })
                
                # Settlements (0-1 records, not all contracts have settlements)
                if random.random() > 0.5:
                    await session.execute(text("""
                        INSERT INTO project_settlements 
                        (contract_id, settlement_code, settlement_date, completion_date, 
                         settlement_amount, status, description, created_by)
                        VALUES (:cid, :code, :sd, :cd, :amt, :stat, :desc, :cb)
                    """), {
                        'cid': uid,
                        'code': f'SET-2025-{uid:03d}',
                        'sd': random_date_2025(),
                        'cd': random_date_2025(),
                        'amt': float(random_amount(500000, 3000000)),
                        'stat': random.choice(['待审核', '已审核', '已完成']),
                        'desc': f'结算记录-合同{uid}',
                        'cb': 1
                    })
            
            await session.commit()
            print("  Upstream financial records created.")
            
            # ========== 3. Downstream Contracts (10) ==========
            print("Creating 10 downstream contracts...")
            for i in range(1, 11):
                sign_date = random_date_2025()
                contract_amount = random_amount(50000, 2000000)
                
                await session.execute(text("""
                    INSERT INTO contracts_downstream 
                    (serial_number, contract_code, contract_name, party_a_name, party_b_name,
                     upstream_contract_id, category, company_category, pricing_mode, management_mode,
                     responsible_person, contract_amount, sign_date, start_date, end_date, status, notes, created_by)
                    VALUES 
                    (:sn, :code, :name, :pa, :pb, :uid, :cat, :cc, :pm, :mm, :rp, :amt, :sd, :st, :ed, :stat, :notes, :cb)
                """), {
                    'sn': i,
                    'code': f'XY-2025{str(i).zfill(2)}-{str(i).zfill(3)}',
                    'name': f'{random.choice(SUPPLIER_NAMES)}供货合同（{i}期）',
                    'pa': random.choice(PARTY_B_NAMES),  # Our company as Party A
                    'pb': random.choice(SUPPLIER_NAMES),  # Supplier as Party B
                    'uid': random.choice(upstream_ids) if upstream_ids else None,
                    'cat': random.choice(DOWNSTREAM_CATEGORIES),
                    'cc': random.choice(COMPANY_CATEGORIES),
                    'pm': random.choice(PRICING_MODES),
                    'mm': random.choice(MANAGEMENT_MODES),
                    'rp': random.choice(RESPONSIBLE_PERSONS),
                    'amt': float(contract_amount),
                    'sd': sign_date,
                    'st': sign_date + timedelta(days=random.randint(7, 30)),
                    'ed': sign_date + timedelta(days=random.randint(90, 180)),
                    'stat': random.choice(CONTRACT_STATUSES),
                    'notes': f'下游合同测试数据{i}',
                    'cb': 1
                })
            
            await session.commit()
            
            # Get downstream IDs
            result = await session.execute(text("SELECT id FROM contracts_downstream ORDER BY id"))
            downstream_ids = [row[0] for row in result.fetchall()]
            print(f"  Created downstream contracts: {downstream_ids}")
            
            # ========== 4. Downstream Financial Records ==========
            print("Creating downstream financial records...")
            for did in downstream_ids:
                # Payables (1-3 records)
                for _ in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_downstream_payables 
                        (contract_id, category, amount, description, expected_date, created_by)
                        VALUES (:cid, :cat, :amt, :desc, :dt, :cb)
                    """), {
                        'cid': did,
                        'cat': random.choice(PAYMENT_CATEGORIES),
                        'amt': float(random_small_amount(10000, 200000)),
                        'desc': f'应付款记录-合同{did}',
                        'dt': random_date_2025(),
                        'cb': 1
                    })
                
                # Invoices (1-3 records)
                for j in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_downstream_invoices 
                        (contract_id, invoice_number, invoice_date, amount, supplier_name, description, created_by)
                        VALUES (:cid, :inv, :dt, :amt, :sn, :desc, :cb)
                    """), {
                        'cid': did,
                        'inv': f'FP-2025-{did:03d}-{j+1:02d}',
                        'dt': random_date_2025(),
                        'amt': float(random_small_amount(10000, 200000)),
                        'sn': random.choice(SUPPLIER_NAMES),
                        'desc': f'收票记录-合同{did}',
                        'cb': 1
                    })
                
                # Payments (1-3 records)
                for _ in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_downstream_payments 
                        (contract_id, payment_date, amount, payment_method, payee_name, description, created_by)
                        VALUES (:cid, :dt, :amt, :pm, :pn, :desc, :cb)
                    """), {
                        'cid': did,
                        'dt': random_date_2025(),
                        'amt': float(random_small_amount(10000, 200000)),
                        'pm': random.choice(['银行转账', '支票', '电汇']),
                        'pn': random.choice(SUPPLIER_NAMES),
                        'desc': f'付款记录-合同{did}',
                        'cb': 1
                    })
                
                # Settlements (0-1 records)
                if random.random() > 0.5:
                    await session.execute(text("""
                        INSERT INTO downstream_settlements 
                        (contract_id, settlement_code, settlement_date, completion_date, 
                         settlement_amount, status, description, created_by)
                        VALUES (:cid, :code, :sd, :cd, :amt, :stat, :desc, :cb)
                    """), {
                        'cid': did,
                        'code': f'XYSET-2025-{did:03d}',
                        'sd': random_date_2025(),
                        'cd': random_date_2025(),
                        'amt': float(random_amount(100000, 1500000)),
                        'stat': random.choice(['待审核', '已审核', '已完成']),
                        'desc': f'结算记录-合同{did}',
                        'cb': 1
                    })
            
            await session.commit()
            print("  Downstream financial records created.")
            
            # ========== 5. Management Contracts (10) ==========
            print("Creating 10 management contracts...")
            for i in range(1, 11):
                sign_date = random_date_2025()
                contract_amount = random_amount(30000, 1000000)
                
                await session.execute(text("""
                    INSERT INTO contracts_management 
                    (serial_number, contract_code, contract_name, party_a_name, party_b_name,
                     upstream_contract_id, category, company_category, pricing_mode, management_mode,
                     responsible_person, contract_amount, sign_date, start_date, end_date, status, notes, created_by)
                    VALUES 
                    (:sn, :code, :name, :pa, :pb, :uid, :cat, :cc, :pm, :mm, :rp, :amt, :sd, :st, :ed, :stat, :notes, :cb)
                """), {
                    'sn': i,
                    'code': f'GL-2025{str(i).zfill(2)}-{str(i).zfill(3)}',
                    'name': f'管理服务合同（{i}期）',
                    'pa': random.choice(PARTY_B_NAMES),
                    'pb': random.choice(['重庆管理咨询公司', '四川项目管理有限公司', '成都工程顾问公司', '重庆监理服务公司', '重庆工程咨询有限公司']),
                    'uid': random.choice(upstream_ids) if upstream_ids else None,
                    'cat': random.choice(['咨询服务', '监理服务', '项目管理', '技术支持', '其他服务']),
                    'cc': random.choice(COMPANY_CATEGORIES),
                    'pm': random.choice(PRICING_MODES),
                    'mm': random.choice(MANAGEMENT_MODES),
                    'rp': random.choice(RESPONSIBLE_PERSONS),
                    'amt': float(contract_amount),
                    'sd': sign_date,
                    'st': sign_date + timedelta(days=random.randint(7, 30)),
                    'ed': sign_date + timedelta(days=random.randint(90, 180)),
                    'stat': random.choice(CONTRACT_STATUSES),
                    'notes': f'管理合同测试数据{i}',
                    'cb': 1
                })
            
            await session.commit()
            
            # Get management IDs
            result = await session.execute(text("SELECT id FROM contracts_management ORDER BY id"))
            management_ids = [row[0] for row in result.fetchall()]
            print(f"  Created management contracts: {management_ids}")
            
            # ========== 6. Management Financial Records ==========
            print("Creating management financial records...")
            for mid in management_ids:
                # Payables (1-3 records)
                for _ in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_management_payables 
                        (contract_id, category, amount, description, expected_date, created_by)
                        VALUES (:cid, :cat, :amt, :desc, :dt, :cb)
                    """), {
                        'cid': mid,
                        'cat': random.choice(PAYMENT_CATEGORIES),
                        'amt': float(random_small_amount(5000, 100000)),
                        'desc': f'应付款记录-管理合同{mid}',
                        'dt': random_date_2025(),
                        'cb': 1
                    })
                
                # Invoices (1-3 records)
                for j in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_management_invoices 
                        (contract_id, invoice_number, invoice_date, amount, description, created_by)
                        VALUES (:cid, :inv, :dt, :amt, :desc, :cb)
                    """), {
                        'cid': mid,
                        'inv': f'GLFP-2025-{mid:03d}-{j+1:02d}',
                        'dt': random_date_2025(),
                        'amt': float(random_small_amount(5000, 100000)),
                        'desc': f'收票记录-管理合同{mid}',
                        'cb': 1
                    })
                
                # Payments (1-3 records)
                for _ in range(random.randint(1, 3)):
                    await session.execute(text("""
                        INSERT INTO finance_management_payments 
                        (contract_id, payment_date, amount, payment_method, payee_name, description, created_by)
                        VALUES (:cid, :dt, :amt, :pm, :pn, :desc, :cb)
                    """), {
                        'cid': mid,
                        'dt': random_date_2025(),
                        'amt': float(random_small_amount(5000, 100000)),
                        'pm': random.choice(['银行转账', '支票', '电汇']),
                        'pn': random.choice(['重庆管理咨询公司', '四川项目管理有限公司', '成都工程顾问公司']),
                        'desc': f'付款记录-管理合同{mid}',
                        'cb': 1
                    })
                
                # Settlements (0-1 records)
                if random.random() > 0.5:
                    await session.execute(text("""
                        INSERT INTO management_settlements 
                        (contract_id, settlement_code, settlement_date, completion_date, 
                         settlement_amount, status, description, created_by)
                        VALUES (:cid, :code, :sd, :cd, :amt, :stat, :desc, :cb)
                    """), {
                        'cid': mid,
                        'code': f'GLSET-2025-{mid:03d}',
                        'sd': random_date_2025(),
                        'cd': random_date_2025(),
                        'amt': float(random_amount(50000, 500000)),
                        'stat': random.choice(['待审核', '已审核', '已完成']),
                        'desc': f'结算记录-管理合同{mid}',
                        'cb': 1
                    })
            
            await session.commit()
            print("  Management financial records created.")
            
            # ========== 7. Non-Contract Expenses (10) ==========
            print("Creating 10 non-contract expenses...")
            for i in range(1, 11):
                await session.execute(text("""
                    INSERT INTO expenses_non_contract 
                    (expense_code, expense_name, category, expense_type, amount, 
                     expense_date, upstream_contract_id, responsible_person, 
                     status, description, created_by)
                    VALUES 
                    (:code, :name, :cat, :et, :amt, :dt, :uid, :rp, :stat, :desc, :cb)
                """), {
                    'code': f'FY-2025{str(i).zfill(2)}-{str(i).zfill(3)}',
                    'name': f'{random.choice(["办公费用", "差旅费用", "培训费用", "会议费用", "材料采购", "设备维护", "车辆使用", "业务招待", "资质办理", "其他费用"])}{i}',
                    'cat': random.choice(EXPENSE_CATEGORIES),
                    'et': random.choice(EXPENSE_TYPES),
                    'amt': float(random_small_amount(1000, 50000)),
                    'dt': random_date_2025(),
                    'uid': random.choice(upstream_ids) if random.random() > 0.3 and upstream_ids else None,
                    'rp': random.choice(RESPONSIBLE_PERSONS),
                    'stat': random.choice(['待审批', '已审批', '已支付']),
                    'desc': f'无合同费用测试数据{i}',
                    'cb': 1
                })
            
            await session.commit()
            print("  Non-contract expenses created.")
            
            # ========== Summary ==========
            print("\n" + "="*50)
            print("Test data population completed!")
            print("="*50)
            
            # Count records
            counts = {}
            for table in ['contracts_upstream', 'contracts_downstream', 'contracts_management', 
                         'expenses_non_contract', 'finance_upstream_receivables', 
                         'finance_upstream_invoices', 'finance_upstream_receipts', 'project_settlements',
                         'finance_downstream_payables', 'finance_downstream_invoices', 
                         'finance_downstream_payments', 'downstream_settlements',
                         'finance_management_payables', 'finance_management_invoices',
                         'finance_management_payments', 'management_settlements']:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()
            
            print("\nRecord counts:")
            for table, count in counts.items():
                print(f"  {table}: {count}")
            
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(populate_data())
