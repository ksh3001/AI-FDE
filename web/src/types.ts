export type RunMode = "auto" | "stepwise";
export type RunStatus =
  | "queued"
  | "parsing"
  | "running"
  | "awaiting_approval"
  | "complete"
  | "failed"
  | "cancelled";

export interface PromptSummary {
  id: string;
  title: string | null;
  version: string;
  stage: string;
  model_role: "generator" | "validator" | "repair";
  output_format: "markdown" | "json";
}

export interface PromptDetail extends PromptSummary {
  body: string;
}

export interface RunCreateResponse {
  run_id: string;
  status: "queued";
}

export interface StageArtifactSummary {
  stage_id: string;
  score: number;
  verdict: "pass" | "fail";
  needs_review: boolean;
  validation_unavailable: boolean;
  created_at: string;
}

export interface RunSummaryResponse {
  run_id: string;
  status: RunStatus;
  mode: RunMode;
  current_stage: string | null;
  failed_stage: string | null;
  failure_reason: string | null;
  created_at: string;
  stage_ids: string[];
  stages: StageArtifactSummary[];
}

export interface ValidationCriterion {
  name: string;
  score: number;
  weight: number;
  comment: string;
}

export interface ValidationIssue {
  severity: "critical" | "major" | "minor";
  location: string;
  problem: string;
  fix: string;
}

export interface ValidationReport {
  overall_score: number;
  verdict: "pass" | "fail";
  criteria: ValidationCriterion[];
  issues: ValidationIssue[];
  repair_instructions: string;
}

export interface AttemptSummary {
  attempt_number: number;
  content: string;
  prompt_id: string;
  prompt_version: string;
  generator_model: string;
  validation_report: ValidationReport | null;
}

export interface StageArtifactResponse {
  stage_id: string;
  content: string;
  prompt_id: string;
  prompt_version: string;
  score: number;
  verdict: "pass" | "fail";
  needs_review: boolean;
  validation_unavailable: boolean;
  created_at: string;
  attempts: AttemptSummary[];
}

export interface SSEEvent {
  seq: number;
  type: string;
  stage_id: string | null;
  data: Record<string, unknown>;
}

export const STAGE_LABELS: Record<string, string> = {
  discovery: "Discovery",
  scqa: "SCQA",
  risk_classification: "Risk Classification",
  prd: "PRD",
  domain_model: "Domain Model",
  feature_specs: "Feature Specs",
  architecture: "Architecture",
  security_model: "Security Model",
  decisions: "Decisions (ADR)",
  compliance_controls: "Compliance Controls",
  technical_design: "Technical Design",
  lean_dmaic: "Lean / DMAIC",
  solution_proposal: "Solution Proposal",
};
