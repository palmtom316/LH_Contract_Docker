from pathlib import Path


def test_frontend_runtime_source_has_no_brand_defaults():
    frontend_root = Path("frontend/src")
    blocked_terms = [
        "蓝海合同管理系统",
        "蓝海合同管理",
        "蓝海合同",
        "蓝海建设集团",
        "重庆蓝海电气工程有限公司",
        "Lanhai Contract System",
        "admin@lanhai.com",
    ]

    matches = []
    for path in frontend_root.rglob("*"):
        if path.is_file() and path.suffix in {".vue", ".js", ".ts"}:
            if "__tests__" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            for term in blocked_terms:
                if term in content:
                    matches.append(f"{path}: {term}")

    assert not matches, "\n".join(matches)
