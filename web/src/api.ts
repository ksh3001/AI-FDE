import type {
  PromptDetail,
  PromptSummary,
  RunCreateResponse,
  RunMode,
  RunSummaryResponse,
  StageArtifactResponse,
} from "./types";

const BASE = "/api";

async function asJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON -- keep statusText
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function listPrompts(): Promise<PromptSummary[]> {
  const res = await fetch(`${BASE}/prompts`);
  const body = await asJson<{ prompts: PromptSummary[] }>(res);
  return body.prompts;
}

export async function getPrompt(id: string): Promise<PromptDetail> {
  const res = await fetch(`${BASE}/prompts/${encodeURIComponent(id)}`);
  return asJson<PromptDetail>(res);
}

export async function createRun(
  useCase: File,
  evidence: File[],
  mode: RunMode,
): Promise<RunCreateResponse> {
  const form = new FormData();
  form.append("use_case", useCase);
  form.append("mode", mode);
  for (const file of evidence) form.append("evidence", file);

  const res = await fetch(`${BASE}/runs`, { method: "POST", body: form });
  return asJson<RunCreateResponse>(res);
}

export async function getRun(runId: string): Promise<RunSummaryResponse> {
  const res = await fetch(`${BASE}/runs/${runId}`);
  return asJson<RunSummaryResponse>(res);
}

export async function getArtifact(runId: string, stageId: string): Promise<StageArtifactResponse> {
  const res = await fetch(`${BASE}/runs/${runId}/artifacts/${stageId}`);
  return asJson<StageArtifactResponse>(res);
}

export async function advanceRun(
  runId: string,
  body: { action: "approve" | "edit" | "regenerate"; content?: string; note?: string },
): Promise<RunSummaryResponse> {
  const res = await fetch(`${BASE}/runs/${runId}/advance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return asJson<RunSummaryResponse>(res);
}

export async function cancelRun(runId: string): Promise<RunSummaryResponse> {
  const res = await fetch(`${BASE}/runs/${runId}/cancel`, { method: "POST" });
  return asJson<RunSummaryResponse>(res);
}

export async function resumeFailedRun(runId: string): Promise<RunSummaryResponse> {
  const res = await fetch(`${BASE}/runs/${runId}/resume`, { method: "POST" });
  return asJson<RunSummaryResponse>(res);
}

export async function reviseStage(runId: string, stageId: string): Promise<RunSummaryResponse> {
  const res = await fetch(`${BASE}/runs/${runId}/revise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage_id: stageId }),
  });
  return asJson<RunSummaryResponse>(res);
}

export function bundleUrl(runId: string): string {
  return `${BASE}/runs/${runId}/bundle`;
}

export function eventsUrl(runId: string): string {
  return `${BASE}/runs/${runId}/events`;
}
