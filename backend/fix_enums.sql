
UPDATE contracts_upstream SET category = 'GENERAL' WHERE category = '总包合同';
UPDATE contracts_upstream SET category = 'SUB_PRO' WHERE category = '专业分包';
UPDATE contracts_upstream SET category = 'SUB_LABOR' WHERE category = '劳务分包';
UPDATE contracts_upstream SET category = 'SERVICE' WHERE category = '技术服务';
UPDATE contracts_upstream SET category = 'MAINTENANCE' WHERE category = '运营维护';
UPDATE contracts_upstream SET category = 'MATERIAL' WHERE category = '物资采购';
UPDATE contracts_upstream SET category = 'OTHER' WHERE category = '其他合同';

UPDATE contracts_upstream SET pricing_mode = 'FIXED_TOTAL' WHERE pricing_mode = '总价包干';
UPDATE contracts_upstream SET pricing_mode = 'FIXED_UNIT' WHERE pricing_mode = '单价包干';
UPDATE contracts_upstream SET pricing_mode = 'LABOR_UNIT' WHERE pricing_mode = '工日单价';
UPDATE contracts_upstream SET pricing_mode = 'RATE_FLOAT' WHERE pricing_mode = '费率下浮';

UPDATE contracts_upstream SET management_mode = 'SELF' WHERE management_mode = '自营';
UPDATE contracts_upstream SET management_mode = 'COOP' WHERE management_mode = '合作';
UPDATE contracts_upstream SET management_mode = 'AFFILIATE' WHERE management_mode = '挂靠';
