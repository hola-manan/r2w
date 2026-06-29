// Wire types matching the P07 backend contract.

export interface Profile {
  id: string;
  name: string;
  radar_count: number;
  compliance_count: number;
}

export type GateStatus = "locked" | "passed" | "needs_review";

export interface ProjectSummary {
  id: string;
  name: string;
  profile_id: string;
  current_stage: number;
  persona: string;
  gate_status: Record<string, GateStatus>;
  stage_names: Record<string, string>;
  project_brief: string;
}

export interface DimensionResult {
  key: string;
  name: string;
  kind: "hard" | "soft";
  level: number;
  rag: "red" | "amber" | "green";
  evidence: string[];
  justification: string;
  followup_question: string | null;
}

export interface Scorecard {
  stage: number;
  dimensions: DimensionResult[];
  weighted_soft: number;
  threshold: number;
  gate_passed: boolean;
  blockers: string[];
  followups: string[];
}

export interface LinkChip {
  to?: string;
  from?: string;
  edge: string;
}

export interface Artifact {
  id: string;
  doc_type: string;
  version: number;
  stale: boolean;
  links_out: LinkChip[];
  links_in: LinkChip[];
  [k: string]: unknown;
}

export interface ImpactItem {
  node_id: string;
  doc_type: string;
  status: string;
  justification: string;
  evidence: string[];
  suggested_patch: Record<string, unknown> | null;
}

export interface ImpactReport {
  changed: string[];
  items: ImpactItem[];
}

export interface TurnResponse {
  reply: string;
  written: Artifact[];
  scorecard: Scorecard;
  escalation: Record<string, unknown> | null;
  impact: ImpactReport | null;
  needs_review: number[];
}

export interface ConfirmResult {
  scorecard: Scorecard;
  advanced: boolean;
  new_stage: number;
  blocked_by_stale: string[]; // node ids holding the gate shut despite a passing rubric
}

export interface AcceptResult {
  node: Artifact;
  impact: ImpactReport; // follow-up pass opened by accepting the patch
}

// An attachment whose contents have been extracted to text server-side and are
// folded into the outgoing message as intent (docx/xlsx).
export interface Attachment {
  filename: string;
  text: string;
}

export type ExtractResult = Attachment;

export interface GraphData {
  nodes: Artifact[];
  edges: { from: string; to: string; edge: string }[];
}
