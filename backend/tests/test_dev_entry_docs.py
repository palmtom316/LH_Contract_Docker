from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_start_dev_script_matches_current_dev_entry_contract():
    script = (REPO_ROOT / "start_dev.ps1").read_text(encoding="utf-8")

    assert "populate_test_data.py" not in script
    assert "http://localhost:3000" in script


def test_requirements_doc_matches_current_dev_entry_contract():
    requirements = (REPO_ROOT / "REQUIREMENTS.md").read_text(encoding="utf-8")

    assert "populate_test_data.py" not in requirements
    assert "http://localhost:3000" in requirements
