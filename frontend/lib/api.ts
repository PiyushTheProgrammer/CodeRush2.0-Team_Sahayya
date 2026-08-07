/**
 * AURA Frontend API Client Library.
 * Interacts with FastAPI research, evidence, stream, export, and governance endpoints.
 */

export interface ResearchStartParams {
  userPrompt: string;
  topK?: number;
  selfEvolve?: boolean;
}

export interface ResearchStartResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  target: string;
  status: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  current_step: string;
  logs: AuditLogItem[];
}

export interface EvidenceLinkItem {
  passage_id: string;
  transformation_type: string;
  source_url?: string;
  content_snippet: string;
  timestamp: string;
  freshness_score?: number;
}

export interface ClaimItem {
  claim_id: string;
  claim_text: string;
  confidence_score: number;
  is_interpretation: boolean;
  evidence_links: EvidenceLinkItem[];
}

export interface EvidenceGraphResponse {
  task_id: string;
  claims: ClaimItem[];
}

export interface PatchEvalRequest {
  target_file_path?: string;
  patch_code: string;
  baseline_version_id?: string;
}

export interface PatchEvalResponse {
  status: string;
  gatekeeper: {
    approved: boolean;
    reason: string;
  };
  benchmark_comparison?: Record<string, any>;
  applied: boolean;
  new_version_id?: string;
}

const API_BASE_URL = "";

/**
 * Initiate LangGraph research pipeline in background.
 */
export async function startResearch(params: ResearchStartParams): Promise<ResearchStartResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_prompt: params.userPrompt,
      top_k: params.topK ?? 5,
      self_evolve: params.selfEvolve ?? true,
    }),
  });

  if (!resp.ok) {
    throw new Error(`Failed starting research task: HTTP ${resp.status}`);
  }
  return resp.json();
}

/**
 * Fetch task status and live audit logs.
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/research/${taskId}/status`);
  if (!resp.ok) {
    throw new Error(`Failed fetching status for task ${taskId}: HTTP ${resp.status}`);
  }
  return resp.json();
}

/**
 * Fetch evidence graph linking claims to citations and timestamps.
 */
export async function getEvidenceGraph(taskId: string): Promise<EvidenceGraphResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/research/${taskId}/evidence`);
  if (!resp.ok) {
    throw new Error(`Failed fetching evidence graph: HTTP ${resp.status}`);
  }
  return resp.json();
}

/**
 * Download compiled ZIP research export package.
 */
export async function downloadExportPackage(taskId: string): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/api/research/${taskId}/export`);
  if (!resp.ok) {
    throw new Error(`Export download failed: HTTP ${resp.status}`);
  }

  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `research_package_${taskId.slice(0, 8)}.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

/**
 * Connect to SSE real-time agent execution stream.
 */
export function streamTaskEvents(
  taskId: string,
  onEvent: (eventData: any) => void,
  onError?: (err: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE_URL}/api/research/${taskId}/stream`);

  eventSource.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      onEvent(parsed);
    } catch (e) {
      console.warn("SSE parse error:", e);
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return () => eventSource.close();
}

/**
 * Evaluate strategy patch against Gatekeeper and Benchmark runner.
 */
export async function evalStrategyPatch(req: PatchEvalRequest): Promise<PatchEvalResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/research/eval-patch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_file_path: req.target_file_path ?? "backend/app/rag/strategies/hybrid_strategy.py",
      patch_code: req.patch_code,
      baseline_version_id: req.baseline_version_id,
    }),
  });

  if (!resp.ok) {
    throw new Error(`Strategy patch evaluation failed: HTTP ${resp.status}`);
  }
  return resp.json();
}
