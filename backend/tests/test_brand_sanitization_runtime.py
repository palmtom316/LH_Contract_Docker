from pathlib import Path


def test_backend_defaults_and_templates_have_no_brand_terms():
    backend_root = Path(__file__).resolve().parents[1]
    files = [
        backend_root / "app/routers/system.py",
        backend_root / "app/routers/auth.py",
        backend_root / "app/routers/contracts_upstream.py",
    ]
    blocked_terms = [
        "蓝海合同管理系统",
        "admin@lanhai.com",
        "重庆蓝海电气",
        "蓝海建设集团",
    ]

    matches = []
    for path in files:
        content = path.read_text(encoding="utf-8")
        for term in blocked_terms:
            if term in content:
                matches.append(f"{path}: {term}")

    assert not matches, "\n".join(matches)
