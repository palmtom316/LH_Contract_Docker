from pathlib import Path


def test_system_router_keeps_authoritative_reset_endpoint():
    system_router = Path("backend/app/routers/system.py")
    content = system_router.read_text(encoding="utf-8")

    assert '@router.post("/reset")' in content
    assert "async def reset_system" in content


def test_backend_router_directory_has_no_orphaned_reset_snippet():
    orphaned_snippet = Path("backend/app/routers/system_reset_snippet.py")

    assert not orphaned_snippet.exists()
