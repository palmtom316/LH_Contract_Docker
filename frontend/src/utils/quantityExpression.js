import { evaluate } from "mathjs";

const EXPRESSION_PATTERN = /^[\d+\-*/.()x×÷\s]+$/i;

export function evaluateQuantityExpression(expression, precision = 3) {
	const raw = String(expression ?? "").trim();
	if (!raw) return null;
	if (!EXPRESSION_PATTERN.test(raw)) return null;

	const normalized = raw
		.replace(/×/g, "*")
		.replace(/÷/g, "/")
		.replace(/x/gi, "*")
		.replace(/\s+/g, "");

	if (!normalized || !/^[\d+\-*/.()]+$/.test(normalized)) return null;

	try {
		const result = evaluate(normalized);
		const value = typeof result === "number" ? result : Number(result);
		if (!Number.isFinite(value)) return null;
		const factor = 10 ** precision;
		return Math.round(value * factor) / factor;
	} catch {
		return null;
	}
}

export function formatQuantity(value, precision = 3) {
	if (value === null || value === undefined || value === "") return "";
	const numeric = Number(value);
	if (!Number.isFinite(numeric)) return "";
	return numeric.toFixed(precision).replace(/\.?0+$/, "");
}
