import enum

class ContractCategory(str, enum.Enum):
    """合同类别"""
    MATERIAL = "材料设备"
    SUB_PRO = "专业分包"
    SUB_LABOR = "劳务分包"
    CONSULTING = "咨询服务"
    SERVICE = "技术服务"
    OTHER = "其他合同"

class PricingMode(str, enum.Enum):
    """计价模式"""
    FIXED_TOTAL = "总价包干"
    FIXED_UNIT = "单价包干"
    LABOR_UNIT = "工日单价"
    RATE_FLOAT = "费率下浮"

class ManagementMode(str, enum.Enum):
    """管理模式"""
    SELF = "自营"
    COOP = "合作"
    AFFILIATE = "挂靠"

class PaymentCategory(str, enum.Enum):
    """应收/付款类别"""
    PREPAYMENT = "预付款"
    PROGRESS = "进度款"
    COMPLETION = "完工款"
    SETTLEMENT = "结算款"
    WARRANTY = "质保金"
    # Note: Requirement 3.1 lists these 5 exactly.

class ReceivableCategory(str, enum.Enum):
    """应收款类别 - 匹配数据库枚举"""
    ADVANCE_PAYMENT = "ADVANCE_PAYMENT"
    PROGRESS_PAYMENT = "PROGRESS_PAYMENT"
    SETTLEMENT_PAYMENT = "SETTLEMENT_PAYMENT"
    RETENTION_MONEY = "RETENTION_MONEY"
    OTHER = "OTHER"


class ExpenseCategory(str, enum.Enum):
    """费用类别"""
    COMPANY = "公司费用"
    PROJECT = "项目费用"

class ExpenseType(str, enum.Enum):
    """费用分类"""
    MANAGEMENT = "管理费"
    TRAINING = "培训费"
    CATERING = "餐饮费"
    TRANSPORT = "交通费"
    CONSULTING = "咨询费"
    BUSINESS = "业务费"
    LEASING = "租赁费"
    QUALIFICATION = "资质费"
    VEHICLE = "车辆使用费"
