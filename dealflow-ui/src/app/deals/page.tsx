"use client";

import { useState } from "react";
import {
  Upload,
  FileText,
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Download,
  Loader2,
  Shield,
  Target,
} from "lucide-react";
import { AnalysisResult } from "@/types";
import { API_V1 } from "@/lib/utils";

type AnalysisStep = "idle" | "extracting" | "analyzing" | "risks" | "valuation" | "done";

export default function DealsPage() {
  const [companyName, setCompanyName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysisStep, setAnalysisStep] = useState<AnalysisStep>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "financials" | "risks" | "valuation">("summary");
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const analyzeFile = async () => {
    if (!selectedFile) {
      setError("Please provide a file to analyze");
      return;
    }

    try {
      setError(null);
      setAnalysisStep("extracting");

      const formData = new FormData();
      formData.append("files", selectedFile);
      if (companyName) {
        formData.append("company_name", companyName);
      }

      // Simulate progress steps while waiting for the API
      const progressTimer1 = setTimeout(() => setAnalysisStep("analyzing"), 3000);
      const progressTimer2 = setTimeout(() => setAnalysisStep("risks"), 8000);
      const progressTimer3 = setTimeout(() => setAnalysisStep("valuation"), 15000);

      const response = await fetch(`${API_V1}/analyze/`, {
        method: "POST",
        body: formData,
      });

      // Clear progress timers
      clearTimeout(progressTimer1);
      clearTimeout(progressTimer2);
      clearTimeout(progressTimer3);

      if (!response.ok) {
        const errBody = await response.text().catch(() => "");
        throw new Error(errBody || "Analysis failed");
      }

      const data: AnalysisResult = await response.json();
      setResult(data);
      setAnalysisStep("done");
    } catch (err: any) {
      setError(err.message || "Failed to analyze deal. Please try again.");
      setAnalysisStep("idle");
      console.error(err);
    }
  };

  const getRecommendationColor = (rec: string) => {
    if (rec.includes("Strong Buy") || rec.includes("Buy")) return "badge-success";
    if (rec.includes("Hold")) return "badge-warning";
    return "badge-danger";
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "text-red-500 bg-red-500/10 border-red-500/30";
      case "high": return "text-orange-400 bg-orange-500/10 border-orange-500/30";
      case "medium": return "text-amber-400 bg-amber-500/10 border-amber-500/30";
      case "low": return "text-green-400 bg-green-500/10 border-green-500/30";
      default: return "text-muted-foreground bg-muted border-border";
    }
  };

  const formatMoney = (val?: number) => {
    if (val === undefined || val === null) return "N/A";
    if (val >= 1000) return `$${(val / 1000).toFixed(1)}B`;
    if (val >= 1) return `$${val.toFixed(1)}M`;
    return `$${(val * 1000).toFixed(0)}K`;
  };

  const steps = [
    { key: "extracting", label: "Extracting" },
    { key: "analyzing", label: "Analyzing" },
    { key: "risks", label: "Risks" },
    { key: "valuation", label: "Valuation" },
    { key: "done", label: "Done" },
  ];

  const getStepIndex = (step: AnalysisStep) => {
    const index = steps.findIndex((s) => s.key === step);
    return index === -1 ? 0 : index;
  };

  const currentStepIndex = getStepIndex(analysisStep);

  const resetAnalysis = () => {
    setResult(null);
    setAnalysisStep("idle");
    setSelectedFile(null);
    setCompanyName("");
    setError(null);
    setActiveTab("summary");
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Analyze Deal</h1>
        <p className="mt-2 text-muted-foreground">
          Upload a pitch deck and get AI-powered analysis
        </p>
      </div>

      {/* Upload Section */}
      {analysisStep === "idle" && (
        <div className="space-y-6">
          <div className="glass-effect rounded-lg border border-border p-6">
            <label className="block text-sm font-medium text-foreground mb-2">
              Company Name (optional)
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Enter company name for better extraction"
              className="input-field w-full"
            />
          </div>

          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="glass-effect rounded-lg border-2 border-dashed border-border p-12 text-center hover:border-primary/50 transition-colors cursor-pointer"
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.docx,.xlsx"
              onChange={handleFileSelect}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium text-foreground mb-2">
                {selectedFile ? selectedFile.name : "Drop pitch deck here or click to upload"}
              </p>
              <p className="text-sm text-muted-foreground">
                Supports PDF, DOCX, XLSX (max 50MB)
              </p>
            </label>
          </div>

          {error && (
            <div className="glass-effect rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <button
            onClick={analyzeFile}
            disabled={!selectedFile}
            className="button-primary w-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <TrendingUp className="h-5 w-5" />
            Analyze Deal
          </button>
        </div>
      )}

      {/* Progress Indicator */}
      {analysisStep !== "idle" && analysisStep !== "done" && (
        <div className="glass-effect rounded-lg border border-border p-8">
          <div className="mb-8 text-center">
            <Loader2 className="mx-auto h-12 w-12 text-primary animate-spin mb-4" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Analyzing {companyName || "Deal"}
            </h2>
            <p className="text-muted-foreground">
              AI agents are processing your documents...
            </p>
          </div>

          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.key} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`h-10 w-10 rounded-full flex items-center justify-center border-2 ${
                      index <= currentStepIndex
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-muted text-muted-foreground"
                    }`}
                  >
                    {index < currentStepIndex ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <span className="text-sm font-semibold">{index + 1}</span>
                    )}
                  </div>
                  <p
                    className={`mt-2 text-sm font-medium ${
                      index <= currentStepIndex
                        ? "text-foreground"
                        : "text-muted-foreground"
                    }`}
                  >
                    {step.label}
                  </p>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 mx-2 ${
                      index < currentStepIndex ? "bg-primary" : "bg-border"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && analysisStep === "done" && (
        <div className="space-y-6">
          {/* Score Header */}
          <div className="glass-effect rounded-lg border border-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-1">
                  {result.summary.company_name}
                </h2>
                <p className="text-muted-foreground mb-3 text-sm">
                  {result.summary.headline}
                </p>
                <div className="flex items-center gap-3">
                  <span
                    className={`badge text-base ${getRecommendationColor(
                      result.summary.recommendation
                    )}`}
                  >
                    {result.summary.recommendation}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    Conviction: {result.summary.conviction}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {result.summary.valuation_range}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-5xl font-bold text-primary mb-1">
                  {result.summary.analysis_score.toFixed(1)}
                </div>
                <p className="text-sm text-muted-foreground">Score / 10</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Risk: {result.summary.risk_score.toFixed(1)}/10
                </p>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="glass-effect rounded-lg border border-border overflow-hidden">
            <div className="border-b border-border flex">
              {[
                { key: "summary", label: "Summary", icon: FileText },
                { key: "financials", label: "Financials", icon: DollarSign },
                { key: "risks", label: "Risks", icon: AlertTriangle },
                { key: "valuation", label: "Valuation", icon: TrendingUp },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`flex-1 px-6 py-4 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                    activeTab === tab.key
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* Summary Tab */}
              {activeTab === "summary" && (
                <div className="space-y-6">
                  {/* Analysis Scores */}
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    {[
                      { label: "Business Model", score: result.analysis.business_model_score },
                      { label: "Market", score: result.analysis.market_score },
                      { label: "Competitive", score: result.analysis.competitive_score },
                      { label: "Growth", score: result.analysis.growth_score },
                    ].map((item) => (
                      <div key={item.label} className="glass-effect rounded-lg border border-border p-4 text-center">
                        <p className="text-sm text-muted-foreground mb-1">{item.label}</p>
                        <p className={`text-2xl font-bold ${
                          item.score.score >= 7 ? "text-green-400" :
                          item.score.score >= 5 ? "text-amber-400" : "text-red-400"
                        }`}>
                          {item.score.score.toFixed(1)}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5 text-green-400" />
                        Reasons to Invest
                      </h3>
                      <ul className="space-y-2">
                        {(result.summary.reasons_to_invest || []).map((reason, idx) => (
                          <li
                            key={idx}
                            className="text-muted-foreground flex items-start gap-2"
                          >
                            <span className="text-green-400 mt-1">+</span>
                            {reason}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-400" />
                        Key Concerns
                      </h3>
                      <ul className="space-y-2">
                        {(result.summary.key_concerns || []).map((concern, idx) => (
                          <li
                            key={idx}
                            className="text-muted-foreground flex items-start gap-2"
                          >
                            <span className="text-amber-400 mt-1">-</span>
                            {concern}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Diligence Priorities */}
                  {result.summary.diligence_priorities?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <Target className="h-5 w-5 text-primary" />
                        Diligence Priorities
                      </h3>
                      <ul className="space-y-2">
                        {result.summary.diligence_priorities.map((item, idx) => (
                          <li key={idx} className="text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-1">{idx + 1}.</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Financials Tab */}
              {activeTab === "financials" && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
                    {[
                      { label: "ARR", value: formatMoney(result.extraction.financials.revenue_arr) },
                      { label: "Growth Rate", value: result.extraction.financials.growth_rate ? `${result.extraction.financials.growth_rate}%` : "N/A" },
                      { label: "Gross Margin", value: result.extraction.financials.gross_margin ? `${result.extraction.financials.gross_margin}%` : "N/A" },
                      { label: "Burn Rate", value: result.extraction.financials.burn_rate ? `$${result.extraction.financials.burn_rate}M/mo` : "N/A" },
                      { label: "Runway", value: result.extraction.financials.runway_months ? `${result.extraction.financials.runway_months} mo` : "N/A" },
                      { label: "Total Raised", value: formatMoney(result.extraction.financials.total_raised) },
                      { label: "Asking", value: formatMoney(result.extraction.financials.asking_amount) },
                      { label: "Valuation Ask", value: formatMoney(result.extraction.financials.valuation_ask) },
                    ].map((metric) => (
                      <div key={metric.label} className="glass-effect rounded-lg border border-border p-4">
                        <p className="text-sm text-muted-foreground mb-1">{metric.label}</p>
                        <p className="text-xl font-bold text-foreground">{metric.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Team */}
                  {result.extraction.team.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-3">
                        Team ({result.extraction.team_size || result.extraction.team.length} members)
                      </h3>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        {result.extraction.team.map((member, idx) => (
                          <div key={idx} className="glass-effect rounded-lg border border-border p-4">
                            <p className="font-semibold text-foreground">{member.name}</p>
                            {member.role && <p className="text-sm text-primary">{member.role}</p>}
                            {member.background && <p className="text-sm text-muted-foreground mt-1">{member.background}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Market */}
                  <div>
                    <h3 className="text-lg font-semibold text-foreground mb-3">Market</h3>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="glass-effect rounded-lg border border-border p-4 text-center">
                        <p className="text-sm text-muted-foreground">TAM</p>
                        <p className="text-xl font-bold text-foreground">
                          {result.extraction.market.tam ? `$${result.extraction.market.tam}B` : "N/A"}
                        </p>
                      </div>
                      <div className="glass-effect rounded-lg border border-border p-4 text-center">
                        <p className="text-sm text-muted-foreground">SAM</p>
                        <p className="text-xl font-bold text-foreground">
                          {result.extraction.market.sam ? `$${result.extraction.market.sam}B` : "N/A"}
                        </p>
                      </div>
                      <div className="glass-effect rounded-lg border border-border p-4 text-center">
                        <p className="text-sm text-muted-foreground">Competitors</p>
                        <p className="text-xl font-bold text-foreground">
                          {result.extraction.market.competitors?.length || 0}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Data Gaps */}
                  {result.extraction.data_gaps?.length > 0 && (
                    <div className="glass-effect rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
                      <h4 className="text-sm font-medium text-amber-400 mb-2">Missing Data Points</h4>
                      <ul className="space-y-1">
                        {result.extraction.data_gaps.map((gap, idx) => (
                          <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                            <AlertTriangle className="h-3 w-3 text-amber-400 mt-1 flex-shrink-0" />
                            {gap}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Risks Tab */}
              {activeTab === "risks" && (
                <div className="space-y-6">
                  {/* Risk Summary */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="glass-effect rounded-lg border border-red-500/30 p-4 text-center">
                      <p className="text-sm text-muted-foreground">Critical</p>
                      <p className="text-2xl font-bold text-red-400">{result.risks.critical_count}</p>
                    </div>
                    <div className="glass-effect rounded-lg border border-orange-500/30 p-4 text-center">
                      <p className="text-sm text-muted-foreground">High</p>
                      <p className="text-2xl font-bold text-orange-400">{result.risks.high_count}</p>
                    </div>
                    <div className="glass-effect rounded-lg border border-amber-500/30 p-4 text-center">
                      <p className="text-sm text-muted-foreground">Medium</p>
                      <p className="text-2xl font-bold text-amber-400">{result.risks.medium_count}</p>
                    </div>
                    <div className="glass-effect rounded-lg border border-green-500/30 p-4 text-center">
                      <p className="text-sm text-muted-foreground">Low</p>
                      <p className="text-2xl font-bold text-green-400">{result.risks.low_count}</p>
                    </div>
                  </div>

                  {/* Deal Breakers */}
                  {result.risks.deal_breakers?.length > 0 && (
                    <div className="glass-effect rounded-lg border border-red-500/30 bg-red-500/5 p-4">
                      <h3 className="text-lg font-semibold text-red-400 mb-2 flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Deal Breakers
                      </h3>
                      <ul className="space-y-2">
                        {result.risks.deal_breakers.map((item, idx) => (
                          <li key={idx} className="text-sm text-red-300">{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Individual Risks */}
                  <div className="space-y-3">
                    {(result.risks.risks || []).map((risk, idx) => (
                      <div
                        key={idx}
                        className={`glass-effect rounded-lg border p-4 ${getSeverityColor(risk.severity)}`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-foreground">{risk.title}</h4>
                          <div className="flex gap-2">
                            <span className={`badge text-xs ${getSeverityColor(risk.severity)}`}>
                              {risk.severity}
                            </span>
                            <span className="badge badge-info text-xs">{risk.category}</span>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">{risk.description}</p>
                        {risk.mitigation && (
                          <p className="text-sm text-green-400 mt-2">
                            Mitigation: {risk.mitigation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Must Verify */}
                  {result.risks.must_verify?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-3">Must Verify in Diligence</h3>
                      <ul className="space-y-2">
                        {result.risks.must_verify.map((item, idx) => (
                          <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                            <Target className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Valuation Tab */}
              {activeTab === "valuation" && (
                <div className="space-y-6">
                  {/* Valuation Range */}
                  <div className="grid grid-cols-3 gap-6">
                    <div className="glass-effect rounded-lg border border-border p-6 text-center">
                      <p className="text-sm text-muted-foreground mb-2">Low</p>
                      <p className="text-3xl font-bold text-red-400">
                        {formatMoney(result.valuation.valuation_low)}
                      </p>
                    </div>
                    <div className="glass-effect rounded-lg border border-primary p-6 text-center">
                      <p className="text-sm text-muted-foreground mb-2">Mid (Base Case)</p>
                      <p className="text-3xl font-bold text-primary">
                        {formatMoney(result.valuation.valuation_mid)}
                      </p>
                    </div>
                    <div className="glass-effect rounded-lg border border-border p-6 text-center">
                      <p className="text-sm text-muted-foreground mb-2">High</p>
                      <p className="text-3xl font-bold text-green-400">
                        {formatMoney(result.valuation.valuation_high)}
                      </p>
                    </div>
                  </div>

                  {/* Ask vs Value */}
                  {result.valuation.company_ask && (
                    <div className="glass-effect rounded-lg border border-border p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Company Ask</p>
                          <p className="text-xl font-bold text-foreground">{formatMoney(result.valuation.company_ask)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Assessment</p>
                          <p className={`text-xl font-bold ${
                            result.valuation.ask_vs_our_value === "Attractive" ? "text-green-400" :
                            result.valuation.ask_vs_our_value === "Fair" ? "text-amber-400" : "text-red-400"
                          }`}>
                            {result.valuation.ask_vs_our_value || "N/A"}
                          </p>
                        </div>
                        {result.valuation.premium_discount_pct !== undefined && (
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">Premium/Discount</p>
                            <p className={`text-xl font-bold ${
                              result.valuation.premium_discount_pct < 0 ? "text-green-400" : "text-red-400"
                            }`}>
                              {result.valuation.premium_discount_pct > 0 ? "+" : ""}
                              {result.valuation.premium_discount_pct.toFixed(1)}%
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Valuation Methods */}
                  {result.valuation.methods?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-3">Valuation Methods</h3>
                      <div className="space-y-3">
                        {result.valuation.methods.map((method, idx) => (
                          <div key={idx} className="glass-effect rounded-lg border border-border p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-semibold text-foreground">{method.method_name}</h4>
                              <p className="text-primary font-bold">
                                {formatMoney(method.value_low)} - {formatMoney(method.value_high)}
                              </p>
                            </div>
                            {method.key_assumptions?.length > 0 && (
                              <ul className="space-y-1">
                                {method.key_assumptions.map((assumption, aidx) => (
                                  <li key={aidx} className="text-sm text-muted-foreground flex items-start gap-2">
                                    <span className="text-muted-foreground mt-1">-</span>
                                    {assumption}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button className="button-primary flex-1 flex items-center justify-center gap-2">
              <Download className="h-5 w-5" />
              Export Analysis Report
            </button>
            <button
              onClick={resetAnalysis}
              className="button-secondary px-6"
            >
              Analyze Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
