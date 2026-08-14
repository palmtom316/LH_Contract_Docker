import { describe, expect, it } from "vitest";
import {
	evaluateQuantityExpression,
	formatQuantity,
} from "../quantityExpression";

describe("evaluateQuantityExpression", () => {
	it("evaluates plus minus multiply divide and keeps 3 decimals", () => {
		expect(evaluateQuantityExpression("1+2*3", 3)).toBe(7);
		expect(evaluateQuantityExpression("10/3", 3)).toBe(3.333);
		expect(evaluateQuantityExpression("2×1.25", 3)).toBe(2.5);
		expect(evaluateQuantityExpression("8÷3", 3)).toBe(2.667);
	});

	it("rejects unsafe or empty expressions", () => {
		expect(evaluateQuantityExpression("")).toBeNull();
		expect(evaluateQuantityExpression("alert(1)")).toBeNull();
		expect(evaluateQuantityExpression("1+abc")).toBeNull();
	});
});

describe("formatQuantity", () => {
	it("formats numeric values", () => {
		expect(formatQuantity(2.5, 3)).toBe("2.5");
		expect(formatQuantity(10, 3)).toBe("10");
	});
});
