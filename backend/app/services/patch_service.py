import difflib
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any
from app.services.repo_service import validate_safe_path, is_allowed_file
from app.schemas.models import FileChange

class PatchService:
    @staticmethod
    def parse_patch_blocks(raw_patch_text: str) -> List[Dict[str, str]]:
        """
        Parses structured patch blocks from model output.
        Accepts formats like:
        --- FILE: path/to/file.py ---
        <<<<< SEARCH
        old_lines
        =====
        new_lines
        >>>>>
        or full file replacements:
        --- FILE: path/to/file.py ---
        ```python
        new_content
        ```
        """
        changes = []
        file_blocks = re.split(r"(?m)^---\s*FILE:\s*([^\n\r]+)\s*---", raw_patch_text)
        if len(file_blocks) > 1:
            for i in range(1, len(file_blocks), 2):
                file_path = file_blocks[i].strip()
                content = file_blocks[i+1].strip()
                # Clean markdown backticks if wrapped
                cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", content)
                cleaned = re.sub(r"\n```$", "", cleaned)
                changes.append({
                    "file_path": file_path,
                    "content": cleaned
                })
        return changes

    @staticmethod
    def apply_file_change(repo_dir: Path, rel_path: str, new_content: str) -> Tuple[bool, str, str]:
        """
        Applies changes safely to a file within repo_dir.
        Returns: (success, unified_diff, error_message)
        """
        target = (repo_dir / rel_path).resolve()
        if not validate_safe_path(repo_dir, target):
            return False, "", f"Path traversal blocked: {rel_path}"
        if not is_allowed_file(target):
            return False, "", f"Cannot edit restricted/excluded file: {rel_path}"
        
        target.parent.mkdir(parents=True, exist_ok=True)
        old_content = ""
        if target.exists():
            old_content = target.read_text(encoding="utf-8", errors="replace")
        
        # Calculate unified diff
        diff_lines = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}"
        ))
        unified_diff = "".join(diff_lines)
        
        # Write new content
        target.write_text(new_content, encoding="utf-8")
        return True, unified_diff, ""
