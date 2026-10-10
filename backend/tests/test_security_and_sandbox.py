import pytest
from pathlib import Path
from app.services.repo_service import validate_safe_path, is_allowed_file, RepositoryService
from app.services.patch_service import PatchService
from app.services.sandbox_service import SandboxService

def test_validate_safe_path():
    base = Path("C:/test/repo")
    safe_target = Path("C:/test/repo/src/module.py")
    unsafe_target = Path("C:/test/repo/../../windows/system32")

    assert validate_safe_path(base, safe_target) is True
    assert validate_safe_path(base, unsafe_target) is False

def test_is_allowed_file():
    assert is_allowed_file(Path("pricing.py")) is True
    assert is_allowed_file(Path(".env")) is False
    assert is_allowed_file(Path("venv/lib/test.py")) is False
    assert is_allowed_file(Path("secret.pem")) is False

def test_parse_patch_blocks():
    sample_text = (
        "Here is the fix:\n"
        "--- FILE: src/calc.py ---\n"
        "```python\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "```\n"
    )
    blocks = PatchService.parse_patch_blocks(sample_text)
    assert len(blocks) == 1
    assert blocks[0]["file_path"] == "src/calc.py"
    assert "def add(a, b):" in blocks[0]["content"]

def test_sandbox_disallowed_command():
    res = SandboxService.execute_test(Path("."), custom_cmd="rmdir /s /q C:\\")
    assert res.exit_code == 126
    assert "Security rejection" in res.stderr
