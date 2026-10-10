import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.schemas.models import (
    TaskRecord, TaskStatus, TestStatus, IssueIntake, AgentPlan, PatchAttempt
)
from app.services.repo_service import RepositoryService
from app.services.sandbox_service import SandboxService
from app.services.agent_service import AgentService
from app.services.report_service import ReportService

router = APIRouter(prefix="/tasks", tags=["Tasks & Workflow"])

# In-memory storage for MVP tasks (could be SQLite in future)
TASKS_DB: Dict[str, TaskRecord] = {}
TASK_WORKSPACES: Dict[str, Path] = {}

@router.get("", response_model=List[TaskRecord])
def list_tasks():
    return list(TASKS_DB.values())

@router.get("/{task_id}", response_model=TaskRecord)
def get_task(task_id: str):
    if task_id not in TASKS_DB:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS_DB[task_id]

@router.post("/create", response_model=TaskRecord)
async def create_task(
    title: str = Form(...),
    description: str = Form(...),
    expected_behavior: Optional[str] = Form(None),
    actual_behavior: Optional[str] = Form(None),
    repo_source: str = Form("bundled"),
    zip_file: Optional[UploadFile] = File(None)
):
    task_id = str(uuid.uuid4())[:8]
    issue = IssueIntake(
        title=title,
        description=description,
        expected_behavior=expected_behavior,
        actual_behavior=actual_behavior,
        repo_source=repo_source
    )

    if repo_source == "bundled":
        source_dir = RepositoryService.get_bundled_repo_path()
        repo_name = "buggy_python_demo"
    elif repo_source == "uploaded_zip" and zip_file:
        zip_bytes = await zip_file.read()
        temp_repo = Path(__file__).parent.parent.parent.parent / "workspaces" / f"upload_{task_id}"
        RepositoryService.extract_zip_safely(zip_bytes, temp_repo)
        source_dir = temp_repo
        repo_name = zip_file.filename or "uploaded_repo"
    else:
        raise HTTPException(status_code=400, detail="Invalid repository source or missing file.")

    workspace = SandboxService.prepare_disposable_workspace(source_dir, task_id)
    TASK_WORKSPACES[task_id] = workspace

    task = TaskRecord(
        id=task_id,
        created_at=datetime.utcnow().isoformat(),
        status=TaskStatus.QUEUED,
        repo_name=repo_name,
        issue=issue,
        model_used=settings.nebius_model
    )
    TASKS_DB[task_id] = task
    return task

@router.post("/{task_id}/analyze", response_model=TaskRecord)
def analyze_task(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = TASK_WORKSPACES.get(task_id)
    if not workspace or not workspace.exists():
        raise HTTPException(status_code=400, detail="Workspace does not exist")

    task.status = TaskStatus.ANALYZING
    plan = AgentService.analyze_and_plan(task, workspace)
    task.plan = plan
    task.status = TaskStatus.PLANNING
    return task

@router.post("/{task_id}/patch", response_model=TaskRecord)
def patch_task(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = TASK_WORKSPACES.get(task_id)
    if not workspace or not workspace.exists():
        raise HTTPException(status_code=400, detail="Workspace does not exist")

    task.status = TaskStatus.PATCHING
    patch_attempt = AgentService.generate_patch(task, workspace)
    task.attempts.append(patch_attempt)
    task.status = TaskStatus.TESTING
    return task

@router.post("/{task_id}/test", response_model=TaskRecord)
def test_task(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = TASK_WORKSPACES.get(task_id)
    if not workspace or not workspace.exists():
        raise HTTPException(status_code=400, detail="Workspace does not exist")

    if not task.attempts:
        raise HTTPException(status_code=400, detail="No patch attempt to test")

    current_attempt = task.attempts[-1]
    test_result = SandboxService.execute_test(workspace, attempt=current_attempt.attempt)
    current_attempt.test_result = test_result
    task.final_test_status = test_result.status

    if test_result.status == TestStatus.PASS:
        task.status = TaskStatus.AWAITING_REVIEW
    else:
        # Bounded repair loop: check repair attempts limit
        if task.current_attempt < settings.max_repair_attempts:
            task.status = TaskStatus.REPAIRING
            # Perform bounded repair attempt
            repair_patch = AgentService.generate_patch(
                task, workspace, failure_output=test_result.stdout or test_result.stderr
            )
            # Re-test repaired patch
            retest_result = SandboxService.execute_test(workspace, attempt=repair_patch.attempt)
            repair_patch.test_result = retest_result
            task.attempts.append(repair_patch)
            task.final_test_status = retest_result.status
            task.status = TaskStatus.AWAITING_REVIEW
        else:
            task.status = TaskStatus.AWAITING_REVIEW

    return task

@router.post("/{task_id}/approve", response_model=TaskRecord)
def approve_task(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.APPROVED
    return task

@router.post("/{task_id}/reject", response_model=TaskRecord)
def reject_task(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.REJECTED
    return task

@router.get("/{task_id}/report", response_class=PlainTextResponse)
def get_report(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ReportService.generate_markdown_report(task)

@router.get("/{task_id}/patch-diff", response_class=PlainTextResponse)
def get_patch_diff(task_id: str):
    task = TASKS_DB.get(task_id)
    if not task or not task.attempts:
        raise HTTPException(status_code=404, detail="No patch found")
    return task.attempts[-1].unified_diff
