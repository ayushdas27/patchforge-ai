import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings
from app.services.nebius_client import nebius_client
from app.services.repo_service import RepositoryService
from app.services.patch_service import PatchService
from app.services.sandbox_service import SandboxService
from app.schemas.models import (
    TaskRecord, TaskStatus, TestStatus, AgentPlan, PatchAttempt, FileChange, IssueIntake
)

logger = logging.getLogger("patchforge.agent")

class AgentService:
    @staticmethod
    def analyze_and_plan(task: TaskRecord, workspace_dir: Path) -> AgentPlan:
        """Calls Nebius Token Factory with NVIDIA Nemotron to generate a structured analysis and fix plan."""
        files = RepositoryService.list_files(workspace_dir)
        repo_tree = "\n".join([f"- {f['path']} ({f['size']} bytes)" for f in files])
        
        # Read contents of candidate files
        sources = []
        for f in files:
            try:
                content = RepositoryService.read_file(workspace_dir, f["path"])
                sources.append(f"=== FILE: {f['path']} ===\n{content}\n")
            except Exception:
                pass
        sources_text = "\n".join(sources)

        system_prompt = (
            "You are PATCHFORGE AI, an expert agentic software engineer using NVIDIA Nemotron. "
            "Your task is to analyze the reported bug in the repository, identify the root cause, "
            "and create a step-by-step repair plan. "
            "Respond in JSON format conforming strictly to this structure:\n"
            "{\n"
            '  "summary": "Short 1-line summary",\n'
            '  "root_cause_hypothesis": "Clear explanation of the bug",\n'
            '  "evidence_files": ["list", "of", "files"],\n'
            '  "proposed_files_to_modify": ["list", "of", "files"],\n'
            '  "test_strategy": "How to verify the fix",\n'
            '  "steps": ["Step 1", "Step 2"],\n'
            '  "risks": ["Potential regressions"]\n'
            "}"
        )

        user_prompt = (
            f"Bug Title: {task.issue.title}\n"
            f"Bug Description: {task.issue.description}\n"
            f"Expected Behavior: {task.issue.expected_behavior or 'N/A'}\n"
            f"Actual Behavior: {task.issue.actual_behavior or 'N/A'}\n\n"
            f"Repository Files:\n{repo_tree}\n\n"
            f"Source Contents:\n{sources_text}"
        )

        client = nebius_client.get_client()
        response = client.chat.completions.create(
            model=task.model_used,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1500
        )

        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
            return AgentPlan(
                summary=data.get("summary", "Analysis completed."),
                root_cause_hypothesis=data.get("root_cause_hypothesis", "Bug located in calculations."),
                evidence_files=data.get("evidence_files", []),
                proposed_files_to_modify=data.get("proposed_files_to_modify", []),
                test_strategy=data.get("test_strategy", "Run pytest test suite."),
                steps=data.get("steps", ["Examine file", "Apply fix", "Run pytest"]),
                risks=data.get("risks", ["None identified"])
            )
        except Exception:
            return AgentPlan(
                summary="Analysis produced unstructured response.",
                root_cause_hypothesis="Likely calculation error.",
                evidence_files=[f["path"] for f in files],
                proposed_files_to_modify=[files[0]["path"]] if files else [],
                test_strategy="Run pytest.",
                steps=["Review diff", "Run tests"],
                risks=["Check edge cases"]
            )

    @staticmethod
    def generate_patch(task: TaskRecord, workspace_dir: Path, failure_output: str = "") -> PatchAttempt:
        """Generates code changes using Nebius Token Factory, applies them to workspace, and captures diff."""
        task.current_attempt += 1
        attempt_num = task.current_attempt

        files = RepositoryService.list_files(workspace_dir)
        sources = []
        for f in files:
            try:
                c = RepositoryService.read_file(workspace_dir, f["path"])
                sources.append(f"--- FILE: {f['path']} ---\n{c}\n")
            except Exception:
                pass
        sources_text = "\n".join(sources)

        system_prompt = (
            "You are PATCHFORGE AI. You are generating a minimal, focused fix for the bug.\n"
            "Output the updated files in this exact format:\n"
            "--- FILE: relative/path/to/file.py ---\n"
            "```python\n"
            "<complete updated file contents>\n"
            "```\n"
            "Provide ONLY the required file blocks with no extra markdown commentary."
        )

        repair_context = ""
        if failure_output:
            repair_context = (
                f"\nATTENTION: A previous test run FAILED with the following output:\n"
                f"{failure_output}\n"
                f"Please fix the code specifically to resolve this test failure!"
            )

        user_prompt = (
            f"Bug Title: {task.issue.title}\n"
            f"Bug Description: {task.issue.description}\n"
            f"{repair_context}\n\n"
            f"Current Files in Repository:\n{sources_text}"
        )

        client = nebius_client.get_client()
        response = client.chat.completions.create(
            model=task.model_used,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2500
        )

        raw_output = response.choices[0].message.content or ""
        parsed_blocks = PatchService.parse_patch_blocks(raw_output)

        file_changes = []
        unified_diffs = []
        for block in parsed_blocks:
            success, diff, err = PatchService.apply_file_change(
                workspace_dir, block["file_path"], block["content"]
            )
            if success:
                file_changes.append(FileChange(
                    path=block["file_path"],
                    action="modify",
                    diff=diff,
                    explanation="Fix applied by NVIDIA Nemotron model via Nebius"
                ))
                unified_diffs.append(diff)

        full_diff = "\n".join(unified_diffs)
        return PatchAttempt(
            attempt=attempt_num,
            files_changed=file_changes,
            unified_diff=full_diff,
            reasoning=f"Generated patch attempt #{attempt_num}"
        )
