from decimal import Decimal
import pytest
from app.core.errors import ValidationError
from app.database import Base
from app.schemas.bank_receipt import ReceiptAllocationCreate
from datetime import datetime
from app.services.bank_receipt import _json_safe, chinese_money_to_decimal, determine_direction, parse_receipt_text, validate_receipt_allocation_total, validate_receipt_confirm_state
from app.schemas.zero_hour_labor import ZeroHourInvoiceCreate, ZeroHourPayableCreate, ZeroHourPaymentCreate

def test_bank_receipt_and_zero_hour_finance_tables_registered():
    names=set(Base.metadata.tables)
    assert {"bank_receipt_batches","bank_receipt_items","bank_receipt_allocations","bank_receipt_match_candidates","finance_zero_hour_payables","finance_zero_hour_invoices","finance_zero_hour_payments"} <= names

def test_zero_hour_finance_entry_contract_requires_only_unit_date_and_amount():
    payable = ZeroHourPayableCreate(amount=100, expected_date="2026-07-23")
    assert "category" not in payable.model_dump()
    invoice = ZeroHourInvoiceCreate(amount=100, invoice_date="2026-07-23", supplier="下游供应商")
    assert invoice.invoice_number is None
    payment = ZeroHourPaymentCreate(amount=100, payment_date="2026-07-23", payee_name="派工单位")
    assert payment.payment_method is None

    with pytest.raises(ValueError):
        ZeroHourPayableCreate(amount=100)
    with pytest.raises(ValueError):
        ZeroHourInvoiceCreate(amount=100, invoice_date="2026-07-23")
    with pytest.raises(ValueError):
        ZeroHourPaymentCreate(amount=100, payment_date="2026-07-23")

def test_parser_extracts_amount_date_and_serial():
    data=parse_receipt_text("交易日期：2026-07-21 08:30:01 币种及金额：CNY 12,345.67 核心流水号：ABC001")
    assert data["amount"] == Decimal("12345.67")
    assert data["bank_serial_number"] == "ABC001"
    assert data["transaction_at"].year == 2026

def test_direction_uses_company_accounts_not_summary_words():
    assert determine_direction({"62220001"},"10001","62220001") == "receipt"
    assert determine_direction({"62220001"},"62220001","10001") == "payment"
    assert determine_direction({"62220001"},"10001","20002") == "unknown"

def test_chinese_money_validation_and_party_fields():
    assert chinese_money_to_decimal("壹万贰仟叁佰肆拾伍元陆角柒分") == Decimal("12345.67")
    data=parse_receipt_text("付款方名称：甲公司\n付款方账号：10001\n收款方名称：乙公司\n收款方账号：20002\n币种及金额：CNY 100.00\n人民币大写：玖拾玖元整")
    assert data["payer_name"] == "甲公司"
    assert data["payee_account"] == "20002"
    assert data["amount_consistent"] is False

def test_receipt_allocation_must_equal_document_total():
    validate_receipt_allocation_total(Decimal("100.00"),[Decimal("40"),Decimal("60")])
    with pytest.raises(ValidationError): validate_receipt_allocation_total(Decimal("100.00"),[Decimal("99.99")])

def test_receipt_and_payment_contract_target_rules():
    ReceiptAllocationCreate(direction="receipt",upstream_contract_id=1,amount=1)
    ReceiptAllocationCreate(direction="payment",downstream_contract_id=1,amount=1)
    ReceiptAllocationCreate(direction="payment",management_contract_id=1,amount=1)
    with pytest.raises(ValueError): ReceiptAllocationCreate(direction="receipt",downstream_contract_id=1,amount=1)
    with pytest.raises(ValueError): ReceiptAllocationCreate(direction="payment",upstream_contract_id=1,amount=1)

def test_parsed_receipt_payload_is_json_safe():
    payload = _json_safe({"amount": Decimal("12.34"), "transaction_at": datetime(2026, 7, 22, 9, 0)})
    assert payload == {"amount": "12.34", "transaction_at": "2026-07-22T09:00:00"}

def test_bank_receipt_has_separate_ignore_and_clear_audit_fields():
    columns = Base.metadata.tables["bank_receipt_items"].columns
    assert {"ignored_reason", "ignored_by", "ignored_at", "clear_reason", "cleared_by", "cleared_at"} <= set(columns.keys())

@pytest.mark.parametrize("status", ["uploaded", "processing", "needs_review", "failed", "ignored", "cleared"])
def test_receipt_confirm_rejects_non_ready_states(status):
    with pytest.raises(ValidationError):
        validate_receipt_confirm_state(status, 1)

def test_receipt_confirm_requires_at_least_one_draft_allocation():
    with pytest.raises(ValidationError):
        validate_receipt_confirm_state("ready", 0)
    validate_receipt_confirm_state("ready", 1)
