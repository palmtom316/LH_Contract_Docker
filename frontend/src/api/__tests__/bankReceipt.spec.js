import { describe, expect, it, vi } from "vitest";
import request from "@/utils/request";
import { uploadReceipt } from "@/api/bankReceipt";

vi.mock("@/utils/request", () => ({
  default: { post: vi.fn(() => Promise.resolve({ ok: true })) },
}));

describe("bank receipt upload api", () => {
  it("sends the selected PDF as the multipart file field", () => {
    const file = new File(["pdf"], "receipt.pdf", { type: "application/pdf" });

    uploadReceipt(file);

    const [url, form] = request.post.mock.calls[0];
    expect(url).toBe("/bank-receipts/batches");
    expect(form).toBeInstanceOf(FormData);
    expect(form.get("file")).toBe(file);
  });
});
