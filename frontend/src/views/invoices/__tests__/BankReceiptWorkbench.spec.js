import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import BankReceiptWorkbench from "../BankReceiptWorkbench.vue";

const { confirmMock, deleteBatchMock, listBatchesMock } = vi.hoisted(() => ({
  confirmMock: vi.fn().mockResolvedValue("confirm"),
  deleteBatchMock: vi.fn().mockResolvedValue(),
  listBatchesMock: vi.fn().mockResolvedValue([
    {
      id: 17,
      batch_number: "BR-20260723-TEST",
      original_filename: "receipt.pdf",
      status: "completed",
    },
  ]),
}));

vi.mock("element-plus", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ElMessageBox: { confirm: confirmMock, prompt: vi.fn() },
  };
});

vi.mock("@/api/bankReceipt", () => ({
  clearReceipt: vi.fn(),
  confirmReceipt: vi.fn(),
  createReceiptAllocation: vi.fn(),
  deleteReceiptAllocation: vi.fn(),
  deleteReceiptBatch: deleteBatchMock,
  deleteFailedReceipt: vi.fn(),
  fetchReceiptFile: vi.fn(),
  ignoreReceipt: vi.fn(),
  listReceiptBatches: listBatchesMock,
  listReceiptItems: vi.fn().mockResolvedValue([]),
  retryReceipt: vi.fn(),
  reviewReceipt: vi.fn(),
  searchReceiptContracts: vi.fn().mockResolvedValue([]),
  updateReceiptAllocation: vi.fn(),
  uploadReceipt: vi.fn(),
}));

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));
let wrapper;

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  vi.clearAllMocks();
});

describe("BankReceiptWorkbench batch actions", () => {
  it("uses concise view text and deletes an unposted batch after confirmation", async () => {
    wrapper = mount(BankReceiptWorkbench);
    await flushPromises();

    expect(wrapper.text()).toContain("查看");
    expect(wrapper.text()).toContain("删除");
    expect(wrapper.text()).not.toContain("查看与复核");

    const deleteButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "删除");
    await deleteButton.trigger("click");
    await flushPromises();

    expect(confirmMock).toHaveBeenCalled();
    expect(deleteBatchMock).toHaveBeenCalledWith(17);
    expect(listBatchesMock).toHaveBeenCalledTimes(2);
  });
});
