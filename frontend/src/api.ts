export interface SetupStatus {
  configured: boolean;
  base_url: string;
  model: string;
  key_status: string;
  setup_instructions: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message?: string;
  error?: string;
  hint?: string;
  model: string;
  base_url: string;
  key_status: string;
  response_sample?: string;
}

export interface FileChange {
  path: string;
  action: string;
  diff: string;
  explanation?: string;
}

export interface TestRunRecord {
  attempt: number;
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  status: "PASS" | "FAIL" | "NOT_RUN" | "ERROR";
  start_time: string;
  end_time: string;
  duration_seconds: number;
  timeout: boolean;
}

export interface PatchAttempt {
  attempt: number;
  files_changed: FileChange[];
  unified_diff: string;
  reasoning: string;
  test_result?: TestRunRecord;
  created_at: string;
}

export interface AgentPlan {
  summary: string;
  root_cause_hypothesis: string;
  evidence_files: string[];
  proposed_files_to_modify: string[];
  test_strategy: string;
  steps: string[];
  risks: string[];
}

export interface TaskRecord {
  id: string;
  created_at: string;
  status: "queued" | "analyzing" | "planning" | "patching" | "testing" | "repairing" | "awaiting_review" | "approved" | "rejected" | "failed" | "cancelled";
  repo_name: string;
  issue: {
    title: string;
    description: string;
    expected_behavior?: string;
    actual_behavior?: string;
    repo_source: string;
  };
  plan?: AgentPlan;
  attempts: PatchAttempt[];
  current_attempt: number;
  final_test_status: "PASS" | "FAIL" | "NOT_RUN" | "ERROR";
  model_used: string;
}

const API_BASE = "http://127.0.0.1:8000/api";

export async function fetchSetupStatus(): Promise<SetupStatus> {
  const res = await fetch(`${API_BASE}/setup/status`);
  return res.json();
}

export async function testConnection(): Promise<ConnectionTestResult> {
  const res = await fetch(`${API_BASE}/setup/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
  return res.json();
}

export async function createTask(formData: FormData): Promise<TaskRecord> {
  const res = await fetch(`${API_BASE}/tasks/create`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function analyzeTask(taskId: string): Promise<TaskRecord> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/analyze`, { method: "POST" });
  return res.json();
}

export async function patchTask(taskId: string): Promise<TaskRecord> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/patch`, { method: "POST" });
  return res.json();
}

export async function testTask(taskId: string): Promise<TaskRecord> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/test`, { method: "POST" });
  return res.json();
}

export async function approveTask(taskId: string): Promise<TaskRecord> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/approve`, { method: "POST" });
  return res.json();
}

export async function rejectTask(taskId: string): Promise<TaskRecord> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/reject`, { method: "POST" });
  return res.json();
}

export async function getTaskReport(taskId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/report`);
  return res.text();
}

export async function getPatchDiff(taskId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/patch-diff`);
  return res.text();
}
