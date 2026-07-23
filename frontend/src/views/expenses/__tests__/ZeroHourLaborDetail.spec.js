import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

const source = readFileSync(
  path.resolve(process.cwd(), "src/views/expenses/ZeroHourLaborDetail.vue"),
  "utf-8",
);

describe("zero-hour labor detail workflow", () => {
  it("uses the shared summary cards and exposes the total amount", () => {
    expect(source).toContain("<StatCard title=\"应付款\"");
    expect(source).toContain("<StatCard title=\"已挂账\"");
    expect(source).toContain("<StatCard title=\"已付款\"");
    expect(source).toContain("<StatCard title=\"未付款\"");
    expect(source).toContain("零星用工总金额");
    expect(source).toContain("金额明细");
    expect(source).toContain("prop=\"unit\"");
    expect(source).toContain("prop=\"quantity\"");
    expect(source).toContain("prop=\"unitPrice\"");
    expect(source).toContain("detail.labor.tax_amount");
  });

  it("keeps finance entry fields minimal and removes numeric steppers", () => {
    expect(source).not.toContain('["category", "类别"]');
    expect(source).toContain('["expected_date", "日期", "date"]');
    expect(source).toContain(':controls="false"');
    expect(source).toContain("searchZeroHourSuppliers");
    expect(source).toContain("银行转账");
    expect(source).toContain("payee_name: row.payee_name || labor.dispatch_unit");
  });

  it("returns to the filtered zero-hour labor list", () => {
    expect(source).toContain('@click="returnToList"');
    expect(source).toContain('name: "Expenses"');
    expect(source).toContain('query: { ...route.query, tab: "zeroHourLabor" }');
    expect(source).not.toContain("router.back()");
  });
});
