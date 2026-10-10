from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    PATCHING = "patching"
    TESTING = "testing"
    REPAIRING = "repairing"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TestStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    ERROR = "ERROR"

class IssueIntake(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    repo_source: str = Field(default="bundled", description="'bundled' or 'uploaded_zip'")

class FileChange(BaseModel):
    path: str
    action: str = Field(default="modify", description="'modify', 'add', 'delete'")
    diff: str
    explanation: Optional[str] = None

class TestRunRecord(BaseModel):
    attempt: int
    command: str
    exit_code: int
    stdout: str
    stderr: str
    status: TestStatus
    start_time: str
    end_time: str
    duration_seconds: float
    timeout: bool = False

class PatchAttempt(BaseModel):
    attempt: int
    files_changed: List[FileChange]
    unified_diff: str
    reasoning: str
    test_result: Optional[TestRunRecord] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AgentPlan(BaseModel):
    summary: str
    root_cause_hypothesis: str
    evidence_files: List[str]
    proposed_files_to_modify: List[str]
    test_strategy: str
    steps: List[str]
    risks: List[str]

class TaskRecord(BaseModel):
    id: str
    created_at: str
    status: TaskStatus
    repo_name: str
    issue: IssueIntake
    plan: Optional[AgentPlan] = None
    attempts: List[PatchAttempt] = Field(default_factory=list)
    current_attempt: int = 0
    final_status: Optional[TaskStatus] = None
    final_test_status: TestStatus = TestStatus.NOT_RUN
    audit_logs: List[Dict[str, Any]] = Field(default_factory=list)
    model_used: str
