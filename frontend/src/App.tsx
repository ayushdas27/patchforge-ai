import { useState, useEffect } from 'react';
import { 
  CheckCircle2, AlertCircle, Play, RefreshCw, Terminal, 
  FileCode, Layers, ShieldCheck, Download, ThumbsUp, ThumbsDown
} from 'lucide-react';
import { 
  fetchSetupStatus, testConnection, createTask, 
  analyzeTask, patchTask, testTask, approveTask, rejectTask,
  getTaskReport, getPatchDiff
} from './api';
import type { SetupStatus, ConnectionTestResult, TaskRecord } from './api';

export function App() {
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [testingConn, setTestingConn] = useState(false);
  
  // Task State
  const [currentTask, setCurrentTask] = useState<TaskRecord | null>(null);
  const [activeTab, setActiveTab] = useState<'pipeline' | 'diff' | 'tests' | 'report'>('pipeline');
  const [loadingStep, setLoadingStep] = useState<string | null>(null);
  
  // Bug form
  const [title, setTitle] = useState("Discount calculation deducts entire percentage instead of proportion");
  const [description, setDescription] = useState("When calculate_discount(50.0, 20.0) is called, it returns 30.0 instead of 40.0. The code subtracts the discount percentage directly from price.");
  const [expectedBehavior, setExpectedBehavior] = useState("50.0 with 20% discount should return 40.0");
  const [actualBehavior, setActualBehavior] = useState("Returns 30.0 (fails test_calculate_discount_twenty_percent)");
  const [reportMarkdown, setReportMarkdown] = useState<string>("");
  const [patchDiffText, setPatchDiffText] = useState<string>("");

  useEffect(() => {
    fetchSetupStatus().then(setSetup).catch(console.error);
  }, []);

  const handleTestConnection = async () => {
    setTestingConn(true);
    setTestResult(null);
    try {
      const res = await testConnection();
      setTestResult(res);
      const updatedSetup = await fetchSetupStatus();
      setSetup(updatedSetup);
    } catch (e: any) {
      setTestResult({
        success: false,
        error: e.message || "Failed to contact backend",
        model: setup?.model || "nvidia/Nemotron-3-Ultra-550b-a55b",
        base_url: setup?.base_url || "",
        key_status: "Error"
      });
    } finally {
      setTestingConn(false);
    }
  };

  const handleCreateTask = async () => {
    setLoadingStep("Creating workspace...");
    try {
      const form = new FormData();
      form.append("title", title);
      form.append("description", description);
      form.append("expected_behavior", expectedBehavior);
      form.append("actual_behavior", actualBehavior);
      form.append("repo_source", "bundled");
      
      const task = await createTask(form);
      setCurrentTask(task);
      setActiveTab('pipeline');
    } catch (e: any) {
      alert("Error creating task: " + e.message);
    } finally {
      setLoadingStep(null);
    }
  };

  const handleAnalyze = async () => {
    if (!currentTask) return;
    setLoadingStep("Analyzing repository with NVIDIA Nemotron via Nebius...");
    try {
      const updated = await analyzeTask(currentTask.id);
      setCurrentTask(updated);
    } catch (e: any) {
      alert("Analysis error: " + e.message);
    } finally {
      setLoadingStep(null);
    }
  };

  const handleGeneratePatch = async () => {
    if (!currentTask) return;
    setLoadingStep("Synthesizing patch with NVIDIA Nemotron...");
    try {
      const updated = await patchTask(currentTask.id);
      setCurrentTask(updated);
      const diff = await getPatchDiff(updated.id);
      setPatchDiffText(diff);
      setActiveTab('diff');
    } catch (e: any) {
      alert("Patch generation error: " + e.message);
    } finally {
      setLoadingStep(null);
    }
  };

  const handleRunTests = async () => {
    if (!currentTask) return;
    setLoadingStep("Executing isolated tests in disposable sandbox...");
    try {
      const updated = await testTask(currentTask.id);
      setCurrentTask(updated);
      const diff = await getPatchDiff(updated.id);
      setPatchDiffText(diff);
      const rpt = await getTaskReport(updated.id);
      setReportMarkdown(rpt);
      setActiveTab('tests');
    } catch (e: any) {
      alert("Test execution error: " + e.message);
    } finally {
      setLoadingStep(null);
    }
  };

  const handleApprove = async () => {
    if (!currentTask) return;
    const updated = await approveTask(currentTask.id);
    setCurrentTask(updated);
    const rpt = await getTaskReport(updated.id);
    setReportMarkdown(rpt);
  };

  const handleReject = async () => {
    if (!currentTask) return;
    const updated = await rejectTask(currentTask.id);
    setCurrentTask(updated);
    const rpt = await getTaskReport(updated.id);
    setReportMarkdown(rpt);
  };

  const downloadFile = (filename: string, content: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
  };

  const latestAttempt = currentTask?.attempts?.length 
    ? currentTask.attempts[currentTask.attempts.length - 1] 
    : null;

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] font-sans flex flex-col antialiased">
      {/* Top Navbar */}
      <header className="h-12 border-b border-[#30363d] bg-[#161b22] px-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <span className="w-6 h-6 rounded bg-[#21262d] border border-[#30363d] flex items-center justify-center font-mono font-bold text-[#58a6ff] text-xs">
              PF
            </span>
            <span>PATCHFORGE AI</span>
          </div>
          <span className="text-[#30363d]">/</span>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#0d1117] border border-[#30363d] text-xs font-mono text-[#8b949e]">
            <span>repo:</span>
            <span className="text-white font-medium">{currentTask?.repo_name || "buggy_python_demo"}</span>
          </div>
        </div>

        {/* Right Info: Nebius Connection status */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2 font-mono bg-[#21262d] px-2.5 py-1 rounded border border-[#30363d]">
            <span className={`w-2 h-2 rounded-full ${setup?.configured ? 'bg-[#3fb950]' : 'bg-[#f85149]'}`}></span>
            <span className="text-[#8b949e]">Nebius Token Factory:</span>
            <span className="text-white truncate max-w-[200px]">{setup?.model || "Nemotron-3-Ultra"}</span>
          </div>
          <button 
            onClick={handleTestConnection} 
            disabled={testingConn}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testingConn ? 'animate-spin text-[#58a6ff]' : ''}`} />
            <span>Test Connection</span>
          </button>
        </div>
      </header>

      {/* Sub-header Banner if testResult */}
      {testResult && (
        <div className={`px-4 py-2 text-xs flex items-center justify-between border-b ${testResult.success ? 'bg-[#0e261a] border-[#238636] text-[#3fb950]' : 'bg-[#2b1014] border-[#da3633] text-[#ff7b72]'}`}>
          <div className="flex items-center gap-2">
            {testResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            <span>
              {testResult.success 
                ? `Connection Verified: Nebius Token Factory responded via model ${testResult.model}. Key status: ${testResult.key_status}`
                : `Connection Failed: ${testResult.error} — ${testResult.hint}`}
            </span>
          </div>
          <button onClick={() => setTestResult(null)} className="text-[#8b949e] hover:text-white">✕</button>
        </div>
      )}

      {/* Pipeline Navigation Bar */}
      <nav className="border-b border-[#30363d] bg-[#161b22] px-6 flex items-center justify-between">
        <div className="flex items-center gap-1 -mb-px">
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`px-4 py-2.5 border-b-2 text-xs font-medium flex items-center gap-2 transition-colors ${activeTab === 'pipeline' ? 'border-[#58a6ff] text-white' : 'border-transparent text-[#8b949e] hover:text-[#c9d1d9]'}`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Agent Pipeline</span>
          </button>
          <button
            onClick={() => setActiveTab('diff')}
            className={`px-4 py-2.5 border-b-2 text-xs font-medium flex items-center gap-2 transition-colors ${activeTab === 'diff' ? 'border-[#58a6ff] text-white' : 'border-transparent text-[#8b949e] hover:text-[#c9d1d9]'}`}
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Patch Diff</span>
            {latestAttempt && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-[#21262d] text-[#58a6ff] border border-[#30363d]">
                Attempt #{latestAttempt.attempt}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('tests')}
            className={`px-4 py-2.5 border-b-2 text-xs font-medium flex items-center gap-2 transition-colors ${activeTab === 'tests' ? 'border-[#58a6ff] text-white' : 'border-transparent text-[#8b949e] hover:text-[#c9d1d9]'}`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Sandbox Execution</span>
            {currentTask?.final_test_status && currentTask.final_test_status !== 'NOT_RUN' && (
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${currentTask.final_test_status === 'PASS' ? 'bg-[#0e261a] text-[#3fb950] border border-[#238636]' : 'bg-[#2b1014] text-[#ff7b72] border border-[#da3633]'}`}>
                {currentTask.final_test_status}
              </span>
            )}
          </button>
          <button
            onClick={() => {
              if (currentTask) getTaskReport(currentTask.id).then(setReportMarkdown);
              setActiveTab('report');
            }}
            className={`px-4 py-2.5 border-b-2 text-xs font-medium flex items-center gap-2 transition-colors ${activeTab === 'report' ? 'border-[#58a6ff] text-white' : 'border-transparent text-[#8b949e] hover:text-[#c9d1d9]'}`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Audit Report & Export</span>
          </button>
        </div>

        {/* Global Action Bar */}
        {currentTask && (
          <div className="flex items-center gap-2 py-1.5">
            <span className="text-xs font-mono text-[#8b949e]">Status:</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#21262d] text-white border border-[#30363d] uppercase">
              {currentTask.status}
            </span>
            {currentTask.status === 'awaiting_review' && (
              <>
                <button
                  onClick={handleApprove}
                  className="px-2.5 py-1 rounded bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-medium flex items-center gap-1 shadow-sm"
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                  <span>Approve Patch</span>
                </button>
                <button
                  onClick={handleReject}
                  className="px-2.5 py-1 rounded bg-[#21262d] hover:bg-[#da3633] text-[#f85149] hover:text-white border border-[#30363d] text-xs font-medium flex items-center gap-1"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  <span>Reject</span>
                </button>
              </>
            )}
          </div>
        )}
      </nav>

      {/* Main Workspace Body */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {loadingStep && (
          <div className="mb-6 p-3 rounded bg-[#161b22] border border-[#58a6ff]/40 flex items-center gap-3 text-xs text-[#58a6ff]">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span className="font-mono">{loadingStep}</span>
          </div>
        )}

        {/* TAB 1: PIPELINE / TASK INTAKE & ORCHESTRATION */}
        {activeTab === 'pipeline' && (
          <div className="grid grid-cols-12 gap-6">
            {/* Left Col: Issue Details & Controls */}
            <div className="col-span-12 lg:col-span-5 space-y-4">
              <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4">
                <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#58a6ff]"></span>
                  Bug Report Intake
                </h2>
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="text-[#8b949e] block mb-1">Issue Title</label>
                    <input 
                      type="text" 
                      value={title} 
                      onChange={(e) => setTitle(e.target.value)} 
                      className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2.5 py-1.5 text-[#c9d1d9] focus:border-[#58a6ff] outline-none" 
                    />
                  </div>
                  <div>
                    <label className="text-[#8b949e] block mb-1">Description</label>
                    <textarea 
                      rows={3} 
                      value={description} 
                      onChange={(e) => setDescription(e.target.value)} 
                      className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2.5 py-1.5 text-[#c9d1d9] focus:border-[#58a6ff] outline-none font-mono text-[11px]" 
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[#8b949e] block mb-1">Expected Behavior</label>
                      <input 
                        type="text" 
                        value={expectedBehavior} 
                        onChange={(e) => setExpectedBehavior(e.target.value)} 
                        className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-[#c9d1d9] focus:border-[#58a6ff] outline-none" 
                      />
                    </div>
                    <div>
                      <label className="text-[#8b949e] block mb-1">Actual Behavior</label>
                      <input 
                        type="text" 
                        value={actualBehavior} 
                        onChange={(e) => setActualBehavior(e.target.value)} 
                        className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-[#c9d1d9] focus:border-[#58a6ff] outline-none" 
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-[#30363d] flex gap-2">
                  {!currentTask ? (
                    <button
                      onClick={handleCreateTask}
                      disabled={!!loadingStep}
                      className="w-full py-2 bg-[#1f6feb] hover:bg-[#388bfd] text-white text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Start Investigation Workflow</span>
                    </button>
                  ) : (
                    <div className="grid grid-cols-3 gap-2 w-full">
                      <button
                        onClick={handleAnalyze}
                        disabled={!!loadingStep}
                        className="py-1.5 bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-white text-xs font-medium rounded transition-colors"
                      >
                        1. Analyze & Plan
                      </button>
                      <button
                        onClick={handleGeneratePatch}
                        disabled={!!loadingStep || !currentTask.plan}
                        className="py-1.5 bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-white text-xs font-medium rounded transition-colors disabled:opacity-50"
                      >
                        2. Patch
                      </button>
                      <button
                        onClick={handleRunTests}
                        disabled={!!loadingStep || currentTask.attempts.length === 0}
                        className="py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-medium rounded transition-colors disabled:opacity-50"
                      >
                        3. Run Tests
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Security & Isolation Callout */}
              <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4 text-xs space-y-2">
                <div className="text-white font-semibold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#3fb950]" />
                  <span>Sandbox & Credentials Guardrails</span>
                </div>
                <p className="text-[#8b949e]">
                  - API Key is loaded safely from local <code className="text-[#c9d1d9]">.env</code>.<br />
                  - Tests execute in a disposable copy of the workspace.<br />
                  - Commands are restricted to allowlisted test runners (<code className="text-[#c9d1d9]">pytest</code>).
                </p>
              </div>
            </div>

            {/* Right Col: Timeline & Generated Plan */}
            <div className="col-span-12 lg:col-span-7 space-y-4">
              <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4">
                <h3 className="text-sm font-semibold text-white mb-3">Agent Strategy & Plan</h3>
                {currentTask?.plan ? (
                  <div className="space-y-3 text-xs">
                    <div className="p-2.5 rounded bg-[#0d1117] border border-[#30363d]">
                      <span className="text-[#8b949e] font-mono text-[11px] block">ROOT CAUSE HYPOTHESIS</span>
                      <p className="text-white mt-1">{currentTask.plan.root_cause_hypothesis}</p>
                    </div>
                    <div>
                      <span className="text-[#8b949e] font-mono text-[11px] block mb-1">PROPOSED STEPS</span>
                      <ol className="list-decimal list-inside space-y-1 text-[#c9d1d9] pl-1 font-mono text-[11px]">
                        {currentTask.plan.steps.map((st, i) => (
                          <li key={i}>{st}</li>
                        ))}
                      </ol>
                    </div>
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#30363d] text-[11px] font-mono">
                      <div>
                        <span className="text-[#8b949e]">Files to inspect:</span>
                        <div className="text-white mt-0.5">{currentTask.plan.evidence_files.join(", ") || "pricing.py"}</div>
                      </div>
                      <div>
                        <span className="text-[#8b949e]">Test Strategy:</span>
                        <div className="text-[#3fb950] mt-0.5">{currentTask.plan.test_strategy}</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center text-[#8b949e] text-xs font-mono">
                    Plan will be generated after step 1: "Analyze & Plan".
                  </div>
                )}
              </div>

              {/* Attempts Timeline */}
              {currentTask && currentTask.attempts.length > 0 && (
                <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4">
                  <h3 className="text-sm font-semibold text-white mb-2">Repair Loop Timeline</h3>
                  <div className="space-y-2">
                    {currentTask.attempts.map((att, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-[#0d1117] border border-[#30363d] flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded bg-[#21262d] text-[#58a6ff] font-mono font-bold flex items-center justify-center text-[10px]">
                            #{att.attempt}
                          </span>
                          <span className="text-white font-mono">{att.files_changed.length} file(s) modified</span>
                        </div>
                        <div>
                          {att.test_result ? (
                            <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium ${att.test_result.status === 'PASS' ? 'bg-[#0e261a] text-[#3fb950] border border-[#238636]' : 'bg-[#2b1014] text-[#ff7b72] border border-[#da3633]'}`}>
                              {att.test_result.status} (exit {att.test_result.exit_code})
                            </span>
                          ) : (
                            <span className="text-[#8b949e] font-mono text-[11px]">Awaiting test execution</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: CODE DIFF VIEWER */}
        {activeTab === 'diff' && (
          <div className="bg-[#161b22] border border-[#30363d] rounded-md overflow-hidden">
            <div className="p-3 border-b border-[#30363d] bg-[#21262d] flex items-center justify-between">
              <span className="font-mono text-xs text-white font-medium">Unified Diff (Synthesized by NVIDIA Nemotron)</span>
              <button 
                onClick={() => downloadFile(`patch_attempt_${latestAttempt?.attempt || 1}.diff`, patchDiffText)}
                disabled={!patchDiffText}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] hover:bg-[#30363d] border border-[#30363d] text-white text-xs disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export .diff</span>
              </button>
            </div>
            <pre className="p-4 font-mono text-xs overflow-x-auto leading-relaxed text-[#c9d1d9] bg-[#0d1117] min-h-[300px]">
              {patchDiffText ? patchDiffText.split("\n").map((line, idx) => {
                let color = "text-[#c9d1d9]";
                let bg = "";
                if (line.startsWith("+") && !line.startsWith("+++")) {
                  color = "text-[#3fb950]";
                  bg = "bg-[#0e261a]";
                } else if (line.startsWith("-") && !line.startsWith("---")) {
                  color = "text-[#ff7b72]";
                  bg = "bg-[#2b1014]";
                } else if (line.startsWith("@@")) {
                  color = "text-[#58a6ff]";
                }
                return (
                  <div key={idx} className={`${color} ${bg} px-1 rounded`}>
                    {line}
                  </div>
                );
              }) : (
                <div className="text-[#8b949e]">No patch diff generated yet. Run step 2: "Patch" in the pipeline.</div>
              )}
            </pre>
          </div>
        )}

        {/* TAB 3: TEST RUNNER OUTPUT */}
        {activeTab === 'tests' && (
          <div className="bg-[#161b22] border border-[#30363d] rounded-md overflow-hidden">
            <div className="p-3 border-b border-[#30363d] bg-[#21262d] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-[#58a6ff]" />
                <span className="font-mono text-xs text-white font-medium">Isolated Sandbox Execution Logs</span>
              </div>
              {latestAttempt?.test_result && (
                <span className={`px-2 py-0.5 rounded text-xs font-mono font-medium ${latestAttempt.test_result.status === 'PASS' ? 'bg-[#0e261a] text-[#3fb950] border border-[#238636]' : 'bg-[#2b1014] text-[#ff7b72] border border-[#da3633]'}`}>
                  {latestAttempt.test_result.status} (exit code {latestAttempt.test_result.exit_code})
                </span>
              )}
            </div>
            <div className="p-4 bg-[#0d1117] font-mono text-xs min-h-[300px] overflow-x-auto">
              {latestAttempt?.test_result ? (
                <div>
                  <div className="text-[#8b949e] mb-2 pb-2 border-b border-[#30363d]">
                    Command: <code className="text-white">{latestAttempt.test_result.command}</code> | Duration: {latestAttempt.test_result.duration_seconds}s
                  </div>
                  <pre className="text-[#c9d1d9] whitespace-pre-wrap">
                    {latestAttempt.test_result.stdout || latestAttempt.test_result.stderr}
                  </pre>
                </div>
              ) : (
                <div className="text-[#8b949e]">No tests executed yet. Run step 3: "Run Tests" in the pipeline.</div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: AUDIT REPORT & EXPORT */}
        {activeTab === 'report' && (
          <div className="bg-[#161b22] border border-[#30363d] rounded-md overflow-hidden">
            <div className="p-3 border-b border-[#30363d] bg-[#21262d] flex items-center justify-between">
              <span className="font-mono text-xs text-white font-medium">Traceable Markdown Report</span>
              <button 
                onClick={() => downloadFile(`patchforge_report_${currentTask?.id || 'demo'}.md`, reportMarkdown)}
                disabled={!reportMarkdown}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] hover:bg-[#30363d] border border-[#30363d] text-white text-xs disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Report (.md)</span>
              </button>
            </div>
            <pre className="p-4 font-mono text-xs bg-[#0d1117] text-[#c9d1d9] whitespace-pre-wrap min-h-[300px] overflow-x-auto">
              {reportMarkdown || "No report generated yet. Complete task verification to view report."}
            </pre>
          </div>
        )}
      </main>
    </div>
  );
}
export default App;
