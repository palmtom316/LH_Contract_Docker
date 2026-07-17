from app.schemas.contract_management import (
    ContractManagementUpdate,
    ManagementInvoiceCreate,
    ManagementPaymentCreate,
)


def test_management_contract_update_keeps_minio_file_metadata():
    payload = ContractManagementUpdate(
        contract_file_path="contracts/management/2026/07/demo.pdf",
        contract_file_key="contracts/management/2026/07/demo.pdf",
        contract_file_storage="minio",
    ).model_dump(exclude_unset=True)

    assert payload["contract_file_key"] == payload["contract_file_path"]
    assert payload["contract_file_storage"] == "minio"


def test_management_finance_schemas_keep_minio_file_metadata():
    invoice = ManagementInvoiceCreate(
        contract_id=1,
        invoice_number="INV-001",
        invoice_date="2026-07-17",
        amount="100.00",
        file_path="invoices/management/2026/07/invoice.pdf",
        file_key="invoices/management/2026/07/invoice.pdf",
        storage_provider="minio",
    )
    payment = ManagementPaymentCreate(
        contract_id=1,
        payment_date="2026-07-17",
        amount="100.00",
        file_path="payments/management/2026/07/payment.pdf",
        file_key="payments/management/2026/07/payment.pdf",
        storage_provider="minio",
    )

    assert invoice.file_key == invoice.file_path
    assert invoice.storage_provider == "minio"
    assert payment.file_key == payment.file_path
    assert payment.storage_provider == "minio"
