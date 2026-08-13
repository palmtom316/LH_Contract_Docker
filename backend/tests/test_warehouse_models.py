from app.models.warehouse import (
    Warehouse,
    WarehouseCodeCounter,
    WarehouseDocument,
    WarehouseLedgerEntry,
    WarehouseMaterial,
    WarehouseStockBalance,
)


def test_warehouse_tables_are_registered():
    table_names = {
        Warehouse.__tablename__,
        WarehouseMaterial.__tablename__,
        WarehouseCodeCounter.__tablename__,
        WarehouseDocument.__tablename__,
        WarehouseLedgerEntry.__tablename__,
        WarehouseStockBalance.__tablename__,
    }
    assert table_names == {
        "warehouse_warehouses",
        "warehouse_materials",
        "warehouse_code_counters",
        "warehouse_documents",
        "warehouse_ledger_entries",
        "warehouse_stock_balances",
    }


def test_stock_balance_has_non_negative_check():
    checks = [item.name for item in WarehouseStockBalance.__table__.constraints if getattr(item, "name", None)]
    assert "ck_warehouse_stock_non_negative" in checks
    assert "uq_warehouse_stock_dimension" in checks
