import os
import sys
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from app.config import settings
from app.schemas.models import TestRunRecord, TestStatus
from app.security.redaction import redact_secrets

ALLOWLISTED_COMMANDS = [
    "pytest",
    "python -m pytest",
    "pytest -v",
    "pytest -q"
]

class SandboxService:
    @staticmethod
    def prepare_disposable_workspace(source_repo_dir: Path, task_id: str) -> Path:
        """Copies source repo into an isolated disposable sandbox directory."""
        import tempfile
        workspace_base = Path(tempfile.gettempdir()) / "patchforge_workspaces" / f"task_{task_id}"
        workspace_base.parent.mkdir(parents=True, exist_ok=True)
        if workspace_base.exists():
            shutil.rmtree(workspace_base, ignore_errors=True)
        shutil.copytree(source_repo_dir, workspace_base)
        return workspace_base

    @staticmethod
    def execute_test(workspace_dir: Path, attempt: int = 1, custom_cmd: Optional[str] = None) -> TestRunRecord:
        """Executes allowlisted test suite in the disposable workspace with timeout & secret redaction."""
        cmd = custom_cmd or "pytest"
        
        # Check command allowlist
        cmd_base = cmd.strip()
        if not any(cmd_base.startswith(allowed) for allowed in ALLOWLISTED_COMMANDS):
            return TestRunRecord(
                attempt=attempt,
                command=cmd,
                exit_code=126,
                stdout="",
                stderr=f"Security rejection: Command '{cmd}' is not in the safe allowlist ({ALLOWLISTED_COMMANDS}).",
                status=TestStatus.ERROR,
                start_time=datetime.utcnow().isoformat(),
                end_time=datetime.utcnow().isoformat(),
                duration_seconds=0.0,
                timeout=False
            )

        start_dt = datetime.utcnow()
        t0 = time.time()
        timeout_seconds = settings.test_timeout_seconds

        # Build clean environment without leaking host credentials or API keys
        env_pythonpath = os.pathsep.join([str(workspace_dir.resolve())] + sys.path)
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": env_pythonpath,
            "PYTHONUNBUFFERED": "1"
        }

        # Resolve pytest executable or use sys.executable with sys.path
        venv_python = Path(sys.executable).parent / "pytest.exe"
        if venv_python.exists():
            exec_cmd = [str(venv_python)]
        else:
            # Run pytest directly through Python with current sys.path
            runner_code = (
                "import sys, pytest; "
                f"sys.path.insert(0, {repr(str(workspace_dir.resolve()))}); "
                "sys.exit(pytest.main([]))"
            )
            exec_cmd = [sys.executable, "-c", runner_code]
        
        timed_out = False
        try:
            proc = subprocess.run(
                exec_cmd,
                cwd=str(workspace_dir),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=clean_env
            )
            exit_code = proc.returncode
            raw_stdout = proc.stdout
            raw_stderr = proc.stderr
        except subprocess.TimeoutExpired as te:
            timed_out = True
            exit_code = -1
            raw_stdout = te.stdout or ""
            raw_stderr = f"Execution timed out after {timeout_seconds} seconds."
        except Exception as ex:
            exit_code = 1
            raw_stdout = ""
            raw_stderr = str(ex)

        t1 = time.time()
        end_dt = datetime.utcnow()

        safe_stdout = redact_secrets(raw_stdout)
        safe_stderr = redact_secrets(raw_stderr)

        if exit_code == 0:
            status = TestStatus.PASS
        elif timed_out or exit_code == 126:
            status = TestStatus.ERROR
        else:
            status = TestStatus.FAIL

        return TestRunRecord(
            attempt=attempt,
            command=cmd,
            exit_code=exit_code,
            stdout=safe_stdout,
            stderr=safe_stderr,
            status=status,
            start_time=start_dt.isoformat(),
            end_time=end_dt.isoformat(),
            duration_seconds=round(t1 - t0, 3),
            timeout=timed_out
        )
