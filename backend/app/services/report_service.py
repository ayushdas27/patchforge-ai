from app.schemas.models import TaskRecord, TestStatus
from datetime import datetime

class ReportService:
    @staticmethod
    def generate_markdown_report(task: TaskRecord) -> str:
        lines = [
            f"# PATCHFORGE AI — Patch & Verification Report",
            f"**Task ID:** `{task.id}`  ",
            f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Model / Engine:** `{task.model_used}` via Nebius Token Factory  ",
            f"**Repository:** `{task.repo_name}`  ",
            f"**Final Status:** `{task.status.value}`  ",
            f"**Test Outcome:** `{task.final_test_status.value}`  ",
            "",
            "## 1. Issue Overview",
            f"**Title:** {task.issue.title}  ",
            f"**Description:**",
            f"> {task.issue.description}",
            "",
            "## 2. Root Cause & Plan",
        ]

        if task.plan:
            lines.extend([
                f"- **Summary:** {task.plan.summary}",
                f"- **Hypothesis:** {task.plan.root_cause_hypothesis}",
                f"- **Strategy:** {task.plan.test_strategy}",
                "- **Planned Steps:**"
            ])
            for s in task.plan.steps:
                lines.append(f"  1. {s}")
        else:
            lines.append("*No formal plan recorded.*")

        lines.extend([
            "",
            "## 3. Patch Attempts & Verification Evidence"
        ])

        for attempt in task.attempts:
            lines.extend([
                f"### Attempt #{attempt.attempt}",
                f"- **Files Modified:** {len(attempt.files_changed)}",
            ])
            if attempt.test_result:
                tr = attempt.test_result
                lines.extend([
                    f"- **Command Run:** `{tr.command}`",
                    f"- **Exit Code:** `{tr.exit_code}`",
                    f"- **Status:** `{tr.status.value}` ({tr.duration_seconds}s)",
                    "",
                    "```text",
                    tr.stdout or tr.stderr or "No test output",
                    "```"
                ])
            else:
                lines.append("- **Test Status:** *Tests not yet executed for this attempt*")

            if attempt.unified_diff:
                lines.extend([
                    "",
                    "```diff",
                    attempt.unified_diff,
                    "```",
                    ""
                ])

        lines.extend([
            "---",
            "Generated automatically by PATCHFORGE AI. Human review and explicit approval required prior to merging."
        ])
        return "\n".join(lines)
