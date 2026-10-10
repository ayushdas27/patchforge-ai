import os
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

EXCLUDED_NAMES = {
    ".git", ".env", "venv", ".venv", "__pycache__", "node_modules",
    ".pytest_cache", ".tox", ".idea", ".vscode", "dist", "build"
}

EXCLUDED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".pem", ".key", ".token"
}

MAX_FILE_SIZE_BYTES = 200 * 1024  # 200 KB per source file

def validate_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Ensures target_path resolves strictly inside base_dir to avoid path traversal / zip slip."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return resolved_base in resolved_target.parents or resolved_base == resolved_target
    except Exception:
        return False

def is_allowed_file(file_path: Path) -> bool:
    for part in file_path.parts:
        if part in EXCLUDED_NAMES:
            return False
    if file_path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return False
    return True

class RepositoryService:
    @staticmethod
    def get_bundled_repo_path() -> Path:
        base = Path(__file__).parent.parent.parent.parent / "sample_repos" / "buggy_python_demo"
        return base.resolve()

    @staticmethod
    def extract_zip_safely(zip_bytes: bytes, target_dir: Path) -> List[str]:
        target_dir.mkdir(parents=True, exist_ok=True)
        extracted_files = []
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for member in zf.infolist():
                # Defend against zip-slip
                target_file_path = (target_dir / member.filename).resolve()
                if not validate_safe_path(target_dir, target_file_path):
                    raise ValueError(f"Illegal path traversal detected in zip archive: {member.filename}")
                
                # Check for zip bomb limits
                if member.file_size > 5 * 1024 * 1024:
                    raise ValueError(f"Zip member exceeds 5MB limit: {member.filename}")

                if member.is_dir():
                    target_file_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, open(target_file_path, "wb") as dest:
                        shutil.copyfileobj(source, dest)
                    extracted_files.append(str(target_file_path.relative_to(target_dir)))
        return extracted_files

    @staticmethod
    def list_files(repo_path: Path) -> List[Dict[str, Any]]:
        file_tree = []
        if not repo_path.exists():
            return file_tree
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES]
            for file in files:
                f_path = Path(root) / file
                if is_allowed_file(f_path):
                    rel_path = str(f_path.relative_to(repo_path)).replace("\\", "/")
                    file_tree.append({
                        "path": rel_path,
                        "size": f_path.stat().st_size,
                        "is_test": "test" in rel_path.lower()
                    })
        return file_tree

    @staticmethod
    def read_file(repo_path: Path, rel_path: str) -> str:
        target = (repo_path / rel_path).resolve()
        if not validate_safe_path(repo_path, target):
            raise ValueError(f"Security Violation: Access denied to path outside repository: {rel_path}")
        if not is_allowed_file(target):
            raise ValueError(f"Security Violation: File is excluded: {rel_path}")
        if not target.exists():
            raise FileNotFoundError(f"File not found: {rel_path}")
        if target.stat().st_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File exceeds maximum read size of {MAX_FILE_SIZE_BYTES} bytes")
        return target.read_text(encoding="utf-8", errors="replace")
