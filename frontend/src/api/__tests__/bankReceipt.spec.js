import { describe, expect, it, vi } from "vitest";
import request from "@/utils/request";
import { deleteReceiptBatch, uploadReceipt } from "@/api/bankReceipt";

vi.mock("@/utils/request", () => ({
  default: {
    post: vi.fn(() => Promise.resolve({ ok: true })),
    delete: vi.fn(() => Promise.resolve()),
  },
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

  it("deletes a receipt batch through the batch endpoint", () => {
    deleteReceiptBatch(17);

    expect(request.delete).toHaveBeenCalledWith("/bank-receipts/batches/17");
  });
});
