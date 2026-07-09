from app.main import app


def test_invoice_import_router_is_registered():
    paths = {route.path for route in app.routes}

    assert "/api/v1/invoice-imports/batches" in paths
