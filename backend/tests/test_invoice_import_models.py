from app.database import Base


def test_invoice_import_tables_are_registered():
    table_names = set(Base.metadata.tables.keys())

    assert "invoice_import_batches" in table_names
    assert "invoice_import_items" in table_names
    assert "invoice_import_allocations" in table_names
    assert "invoice_import_match_candidates" in table_names


def test_formal_invoice_trace_columns_are_registered():
    upstream = Base.metadata.tables["finance_upstream_invoices"]
    downstream = Base.metadata.tables["finance_downstream_invoices"]
    management = Base.metadata.tables["finance_management_invoices"]

    assert "source_import_item_id" in upstream.c
    assert "source_import_allocation_id" in upstream.c
    assert "source_import_item_id" in downstream.c
    assert "source_import_allocation_id" in downstream.c
    assert "source_import_item_id" in management.c
    assert "source_import_allocation_id" in management.c
    assert "posting_status" in upstream.c
    assert "original_amount" in upstream.c


def test_invoice_project_name_columns_are_registered():
    items = Base.metadata.tables["invoice_import_items"]

    assert "project_name" in items.c
    assert "construction_project_name" in items.c


def test_invoice_tax_rate_column_is_registered():
    items = Base.metadata.tables["invoice_import_items"]

    assert "tax_rate" in items.c


def test_contract_tax_number_columns_are_registered():
    upstream = Base.metadata.tables["contracts_upstream"]
    downstream = Base.metadata.tables["contracts_downstream"]

    assert "party_a_tax_no" in upstream.c
    assert "party_b_tax_no" in upstream.c
    assert "party_a_tax_no" in downstream.c
    assert "party_b_tax_no" in downstream.c
