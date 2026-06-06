from pathlib import Path


def test_system_router_keeps_authoritative_reset_endpoint():
    backend_root = Path(__file__).resolve().parents[1]
    system_router = backend_root / "app/routers/system.py"
    content = system_router.read_text(encoding="utf-8")

    assert '@router.post("/reset")' in content
    assert "async def reset_system" in content


def test_backend_router_directory_has_no_orphaned_reset_snippet():
    backend_root = Path(__file__).resolve().parents[1]
    orphaned_snippet = backend_root / "app/routers/system_reset_snippet.py"

    assert not orphaned_snippet.exists()
