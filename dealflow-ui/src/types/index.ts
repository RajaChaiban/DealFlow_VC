// =============================================================================
// Deal Types
// =============================================================================

export interface Deal {
  id: string;
  analysis_id?: string;
  company_name: string;
  deck_filename?: string;
  status: string;
  overall_score: number;
  recommendation: string;
  created_at: string;
  updated_at?: string;
  has_result?: boolean;
}

// =============================================================================
// Analysis Result Types (matches backend FullAnalysisResult)
// =============================================================================

export interface CompanyBasics {
  name: string;
  tagline?: string;
  industry?: string;
  stage?: string;
  business_model?: string;
  founded_year?: number;
  headquarters?: string;
  website?: string;
}

export interface FinancialMetrics {
  revenue_arr?: number;
  growth_rate?: number;
  gross_margin?: number;
  burn_rate?: number;
  runway_months?: number;
  total_raised?: number;
  asking_amount?: number;
  valuation_ask?: number;
}

export interface TeamMember {
  name: string;
  role?: string;
  background?: string;
}

export interface MarketInfo {
  tam?: number;
  sam?: number;
  target_customers?: string;
  competitors: string[];
}

export interface ExtractionOutput {
  agent_name: string;
  methodology: string;
  company: CompanyBasics;
  financials: FinancialMetrics;
  team: TeamMember[];
  team_size?: number;
  market: MarketInfo;
  documents_processed: number;
  extraction_confidence: number;
  data_gaps: string[];
}

export interface ScoreWithReasoning {
  score: number;
  reasoning: string;
}

export interface AnalysisOutput {
  agent_name: string;
  methodology: string;
  business_model_score: ScoreWithReasoning;
  market_score: ScoreWithReasoning;
  competitive_score: ScoreWithReasoning;
  growth_score: ScoreWithReasoning;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface Risk {
  category: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  likelihood: string;
  mitigation?: string;
}

export interface RiskOutput {
  agent_name: string;
  methodology: string;
  risks: Risk[];
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  overall_risk_score: number;
  deal_breakers: string[];
  must_verify: string[];
}

export interface ValuationMethod {
  method_name: string;
  value_low: number;
  value_mid: number;
  value_high: number;
  key_assumptions: string[];
}

export interface ValuationOutput {
  agent_name: string;
  methodology: string;
  methods: ValuationMethod[];
  valuation_low: number;
  valuation_mid: number;
  valuation_high: number;
  company_ask?: number;
  ask_vs_our_value?: string;
  premium_discount_pct?: number;
}

export interface DealSummary {
  company_name: string;
  analysis_date: string;
  headline: string;
  recommendation: string;
  conviction: string;
  key_metrics: Record<string, any>;
  analysis_score: number;
  risk_score: number;
  reasons_to_invest: string[];
  key_concerns: string[];
  valuation_range: string;
  valuation_vs_ask?: string;
  diligence_priorities: string[];
  questions_for_founders: string[];
}

export interface AnalysisResult {
  summary: DealSummary;
  extraction: ExtractionOutput;
  analysis: AnalysisOutput;
  risks: RiskOutput;
  valuation: ValuationOutput;
  total_processing_time_seconds: number;
  documents_analyzed: string[];
  model_version: string;
}

// =============================================================================
// Comparison Types
// =============================================================================

export interface ComparisonResult {
  deals: Array<{
    deal_id: string;
    company_name: string;
    overall_score: number;
    recommendation: string;
    rank: number;
    strengths?: string[];
    weaknesses?: string[];
  }>;
  comparison_matrix: Record<string, any>;
  winner: string;
  summary: string;
}

// =============================================================================
// Pipeline Types
// =============================================================================

export interface PipelineDeal {
  analysis_id: string;
  company_name: string;
  stage: string;
  priority: string;
  assigned_to?: string;
  tags: string[];
  notes?: string;
  due_date?: string;
  diligence_checklist: Array<{ item: string; completed: boolean }>;
  diligence_completion_pct: number;
  stage_history: Array<{ stage: string; entered_at: string; exited_at?: string }>;
  created_at: string;
  updated_at: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  deals: PipelineDeal[];
  color: string;
}

export interface PipelineBoard {
  stages: string[];
  board: Record<string, PipelineDeal[]>;
  counts: Record<string, number>;
  total_deals: number;
  active_deals: number;
}

// =============================================================================
// Chat Types
// =============================================================================

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  messages: ChatMessage[];
  analysis_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  sources?: string[];
  follow_up_questions?: string[];
}
