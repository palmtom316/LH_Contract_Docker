from datetime import date, timedelta
from decimal import Decimal

def calculate_contract_status(
    contract, 
    total_settlement: Decimal, 
    total_paid: Decimal, 
    total_planned: Decimal
) -> str:
    """
    Calculates the contract status based on financial and date logic.
    
    Priority (High to Low):
    1. 合同中止 (Suspended): 应收/应付金额=0 且 签订时间 > 1年前
    2. 合同终止 (Terminated/Closed): 结算金额=已付/已收 且 质保到期
    3. 质保到期 (Warranty Expired): 质保到期日期 <= 今天
    4. 已结算 (Settled): 结算办结日期 <= 今天
    5. 已完工 (Completed): 完工日期 <= 今天
    6. 执行中 (In Progress): Default
    """
    today = date.today()
    
    # 1. 合同中止 (Suspended)
    if contract.sign_date and contract.sign_date < (today - timedelta(days=365)):
        if total_planned == 0:
            return "合同中止"
            
    # Get relevant dates from settlements
    if not hasattr(contract, 'settlements') or not contract.settlements:
        # If no settlements, check if it's just 'Performing'
        return "执行中"

    def get_valid_dates(items, attr):
        dates = []
        for x in items:
            val = getattr(x, attr, None)
            if val:
                dates.append(val)
        return dates

    completion_dates = get_valid_dates(contract.settlements, 'completion_date')
    settlement_dates = get_valid_dates(contract.settlements, 'settlement_date')
    warranty_dates = get_valid_dates(contract.settlements, 'warranty_date')
    
    max_completion = max(completion_dates) if completion_dates else None
    max_settlement = max(settlement_dates) if settlement_dates else None
    max_warranty = max(warranty_dates) if warranty_dates else None
    
    # 2. 合同终止 (Terminated/Normal Closure)
    # 结算金额 == 已付款（或已收款）金额 且 质保到期日期超过操作日 (passed)
    # We implicitly assume total_settlement > 0 to be meaningful, but rule implies strict equality.
    is_fully_paid = (total_settlement == total_paid)
    
    if is_fully_paid and max_warranty and max_warranty <= today:
        if total_settlement > 0: # Avoid closing empty contracts automatically unless intended?
            return "合同终止"
        # If settlement is 0 and paid is 0, and warranty passed? Maybe terminated. 
        # But usually 'Terminated' implies successful conclusion.
        # Let's trust the logic: equal amount + warranty passed.
        return "合同终止"
    
    # 3. 质保到期
    if max_warranty and max_warranty <= today:
        return "质保到期"
        
    # 4. 已结算
    if max_settlement and max_settlement <= today:
        return "已结算"
        
    # 5. 已完工
    if max_completion and max_completion <= today:
        return "已完工"
        
    return "执行中"
