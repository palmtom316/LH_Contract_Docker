export const INBOUND_BUSINESS_OPTIONS = [
	{ label: "采购入库", value: "PURCHASE" },
	{ label: "甲供入库", value: "OWNER_SUPPLY" },
	{ label: "领用退回", value: "RETURN" },
	{ label: "拆除回收", value: "DEMOLITION" },
	{ label: "期初", value: "OPENING" },
];

export const OUTBOUND_BUSINESS_OPTIONS = [
	{ label: "领用出库", value: "ISSUE" },
	{ label: "退废旧", value: "SCRAP_RETURN" },
	{ label: "报废", value: "WRITE_OFF" },
	{ label: "废旧处理", value: "SCRAP_DISPOSAL" },
];

export const BUSINESS_TYPE_LABELS = Object.fromEntries(
	[...INBOUND_BUSINESS_OPTIONS, ...OUTBOUND_BUSINESS_OPTIONS].map((item) => [
		item.value,
		item.label,
	]),
);

export const WAREHOUSE_FILE_ACCEPT =
	".pdf,.jpg,.jpeg,.png,image/*,application/pdf";
