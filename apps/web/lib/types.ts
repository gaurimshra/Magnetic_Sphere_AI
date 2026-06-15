export type Signal = {
  id: string;
  company_id: string;
  type: string;
  title: string;
  summary: string;
  source: string;
  strength: number;
  occurred_at: string;
};

export type Company = {
  id: string;
  name: string;
  industry: string;
  region: string;
  stage: string;
  description: string;
  website: string;
  competitors: string[];
  technologies: string[];
};

export type ScoreReason = {
  label: string;
  impact: number;
  evidence: string;
};

export type WorkflowAction = {
  type: string;
  title: string;
  payload: string;
  status: string;
};

export type GraphNode = {
  id: string;
  label: string;
  type: string;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
};

export type Opportunity = {
  id: string;
  company: Company;
  opportunity_type: string;
  score: number;
  confidence: number;
  probability: number;
  summary: string;
  recommended_action: string;
  reasons: ScoreReason[];
  risks: string[];
  signals: Signal[];
  workflow_actions: WorkflowAction[];
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
};

export type Trend = {
  id: string;
  label: string;
  direction: string;
  score: number;
  change: number;
};

export type OutreachEmail = {
  subject: string;
  body: string;
};

export type FundingEvent = {
  title: string;
  summary: string;
  source: string;
  occurred_at: string;
};

export type NewsItem = {
  title: string;
  summary: string;
  source: string;
  occurred_at: string;
};

export type HiringSignal = {
  title: string;
  summary: string;
  source: string;
  strength: number;
  occurred_at: string;
};

export type CompanyIntelligence = {
  company_name: string;
  domain: string;
  industry: string;
  headquarters: string;
  employees: string;
  funding: FundingEvent[];
  investors: string[];
  competitors: string[];
  technologies: string[];
  recent_news: NewsItem[];
  hiring_signals: HiringSignal[];
  overview: string;
};

export type CompanyAnalysis = {
  executive_summary: string;
  swot_analysis: string[];
  growth_signals: string[];
  risks: string[];
  competitive_landscape: string[];
  opportunities: string[];
  ai_recommendations: string[];
};

export type TimelineEvent = {
  id: string;
  title: string;
  summary: string;
  source: string;
  category: string;
  occurred_at: string;
};

export type CompanyReport = {
  id: string;
  company: CompanyIntelligence;
  analysis: CompanyAnalysis;
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  timeline: TimelineEvent[];
  opportunity_score: number;
  confidence: number;
  generated_at: string;
  cached: boolean;
  agent_steps: AgentStep[];
  score_delta: number;
  timeline_delta: number;
  score_alert: string;
};

export type AgentStep = {
  id: string;
  name: string;
  purpose: string;
  status: string;
  input_summary: string;
  output_summary: string;
  duration_ms: number;
};

export type RawCompanySignal = {
  id: string;
  company_key: string;
  company_name: string;
  domain: string;
  provider: string;
  signal_type: string;
  source: string;
  title: string;
  url: string;
  raw_snippet: string;
  raw_payload: Record<string, unknown>;
  extracted_entities: string[];
  confidence: number;
  occurred_at: string;
  captured_at: string;
  dedup_key: string;
  duplicate_of: string | null;
};

export type ReportHistoryItem = {
  id: string;
  company_name: string;
  domain: string;
  generated_at: string;
  opportunity_score: number;
  confidence: number;
  score_delta: number;
  timeline_delta: number;
  alert: string;
};

export type IntegrationStatus = {
  enabled: boolean;
  configured: boolean;
  reachable: boolean;
  checked: boolean;
  detail: string;
  checked_at: string;
};

export type WorkflowActionResult = {
  action: string;
  status: string;
  detail: string;
};
