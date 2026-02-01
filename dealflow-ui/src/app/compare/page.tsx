"use client";

import { useState } from "react";
import {
  Upload,
  X,
  Trophy,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { ComparisonResult } from "@/types";
import { API_V1 } from "@/lib/utils";

interface DealUpload {
  id: string;
  companyName: string;
  file: File | null;
}

export default function ComparePage() {
  const [deals, setDeals] = useState<DealUpload[]>([
    { id: "1", companyName: "", file: null },
    { id: "2", companyName: "", file: null },
  ]);
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const addDeal = () => {
    if (deals.length < 3) {
      setDeals([...deals, { id: Date.now().toString(), companyName: "", file: null }]);
    }
  };

  const removeDeal = (id: string) => {
    if (deals.length > 2) {
      setDeals(deals.filter((d) => d.id !== id));
    }
  };

  const updateDeal = (id: string, updates: Partial<DealUpload>) => {
    setDeals(deals.map((d) => (d.id === id ? { ...d, ...updates } : d)));
  };

  const handleFileSelect = (id: string, file: File) => {
    updateDeal(id, { file });
    setError(null);
  };

  const compareDeals = async () => {
    const validDeals = deals.filter((d) => d.file && d.companyName);
    if (validDeals.length < 2) {
      setError("Please provide at least 2 deals with company names and files");
      return;
    }

    try {
      setError(null);
      setComparing(true);

      const formData = new FormData();
      validDeals.forEach((deal, index) => {
        formData.append(`file_${index}`, deal.file!);
        formData.append(`company_name_${index}`, deal.companyName);
      });

      const response = await fetch(`${API_V1}/compare/`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Comparison failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError("Failed to compare deals. Please try again.");
      console.error(err);
    } finally {
      setComparing(false);
    }
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return "text-amber-400";
    if (rank === 2) return "text-slate-300";
    if (rank === 3) return "text-amber-600";
    return "text-muted-foreground";
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Compare Deals</h1>
        <p className="mt-2 text-muted-foreground">
          Upload multiple deals for side-by-side comparison
        </p>
      </div>

      {/* Upload Section */}
      {!result && (
        <div className="space-y-6">
          {deals.map((deal, index) => (
            <div
              key={deal.id}
              className="glass-effect rounded-lg border border-border p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground">
                  Deal {index + 1}
                </h3>
                {deals.length > 2 && (
                  <button
                    onClick={() => removeDeal(deal.id)}
                    className="text-muted-foreground hover:text-red-400 transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={deal.companyName}
                    onChange={(e) =>
                      updateDeal(deal.id, { companyName: e.target.value })
                    }
                    placeholder="Enter company name"
                    className="input-field w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Pitch Deck
                  </label>
                  <div className="relative">
                    <input
                      type="file"
                      id={`file-${deal.id}`}
                      className="hidden"
                      accept=".pdf,.ppt,.pptx"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          handleFileSelect(deal.id, e.target.files[0]);
                        }
                      }}
                    />
                    <label
                      htmlFor={`file-${deal.id}`}
                      className="flex items-center justify-center gap-3 glass-effect border-2 border-dashed border-border rounded-lg p-6 cursor-pointer hover:border-primary/50 transition-colors"
                    >
                      {deal.file ? (
                        <>
                          <CheckCircle2 className="h-5 w-5 text-green-400" />
                          <span className="text-sm text-foreground">
                            {deal.file.name}
                          </span>
                        </>
                      ) : (
                        <>
                          <Upload className="h-5 w-5 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">
                            Click to upload PDF, PPT, or PPTX
                          </span>
                        </>
                      )}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {deals.length < 3 && (
            <button
              onClick={addDeal}
              className="button-secondary w-full py-3 border-2 border-dashed"
            >
              + Add Another Deal
            </button>
          )}

          {error && (
            <div className="glass-effect rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <button
            onClick={compareDeals}
            disabled={comparing || deals.filter((d) => d.file && d.companyName).length < 2}
            className="button-primary w-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {comparing ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Comparing Deals...
              </>
            ) : (
              <>
                <TrendingUp className="h-5 w-5" />
                Compare Deals
              </>
            )}
          </button>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Winner Banner */}
          <div className="glass-effect rounded-lg border-2 border-primary bg-primary/10 p-8 text-center">
            <Trophy className="mx-auto h-16 w-16 text-primary mb-4" />
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Winner: {result.winner}
            </h2>
            <p className="text-muted-foreground">{result.summary}</p>
          </div>

          {/* Rankings */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {result.deals
              .sort((a, b) => a.rank - b.rank)
              .map((deal) => (
                <div
                  key={deal.deal_id}
                  className={`glass-effect rounded-lg border p-6 ${
                    deal.rank === 1 ? "border-primary" : "border-border"
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-4xl font-bold ${getRankColor(deal.rank)}`}
                        >
                          #{deal.rank}
                        </span>
                        {deal.rank === 1 && (
                          <Trophy className="h-6 w-6 text-amber-400" />
                        )}
                      </div>
                      <h3 className="text-xl font-semibold text-foreground">
                        {deal.company_name}
                      </h3>
                    </div>
                    <div className="text-right">
                      <div
                        className={`text-3xl font-bold ${getScoreColor(
                          deal.overall_score
                        )}`}
                      >
                        {deal.overall_score}
                      </div>
                      <p className="text-xs text-muted-foreground">Score</p>
                    </div>
                  </div>

                  <div
                    className={`badge ${
                      deal.recommendation.includes("Buy")
                        ? "badge-success"
                        : deal.recommendation.includes("Hold")
                        ? "badge-warning"
                        : "badge-danger"
                    } w-full justify-center`}
                  >
                    {deal.recommendation}
                  </div>
                </div>
              ))}
          </div>

          {/* Comparison Matrix */}
          <div className="glass-effect rounded-lg border border-border overflow-hidden">
            <div className="border-b border-border bg-secondary p-4">
              <h3 className="text-lg font-semibold text-foreground">
                Detailed Comparison
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="p-4 text-left text-sm font-semibold text-muted-foreground">
                      Metric
                    </th>
                    {result.deals
                      .sort((a, b) => a.rank - b.rank)
                      .map((deal) => (
                        <th
                          key={deal.deal_id}
                          className="p-4 text-center text-sm font-semibold text-foreground"
                        >
                          {deal.company_name}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.comparison_matrix).map(
                    ([metric, values]) => (
                      <tr key={metric} className="border-b border-border">
                        <td className="p-4 text-sm text-muted-foreground capitalize">
                          {metric.replace(/_/g, " ")}
                        </td>
                        {result.deals
                          .sort((a, b) => a.rank - b.rank)
                          .map((deal, idx) => {
                            const value = (values as any)[idx];
                            const isHighest =
                              typeof value === "number" &&
                              value === Math.max(...(values as number[]));
                            return (
                              <td
                                key={deal.deal_id}
                                className={`p-4 text-center text-sm font-medium ${
                                  isHighest ? "text-green-400" : "text-foreground"
                                }`}
                              >
                                {typeof value === "number"
                                  ? value.toFixed(1)
                                  : value}
                              </td>
                            );
                          })}
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {result.deals
              .sort((a, b) => a.rank - b.rank)
              .map((deal) => (
                <div
                  key={deal.deal_id}
                  className="glass-effect rounded-lg border border-border p-6"
                >
                  <h3 className="text-lg font-semibold text-foreground mb-4">
                    {deal.company_name}
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-green-400 mb-2 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Strengths
                      </h4>
                      <ul className="space-y-1">
                        {["Strong market position", "Proven revenue model", "Experienced team"].map(
                          (strength, idx) => (
                            <li
                              key={idx}
                              className="text-sm text-muted-foreground flex items-start gap-2"
                            >
                              <CheckCircle2 className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                              {strength}
                            </li>
                          )
                        )}
                      </ul>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
                        <TrendingDown className="h-4 w-4" />
                        Weaknesses
                      </h4>
                      <ul className="space-y-1">
                        {["High customer acquisition cost", "Limited market data"].map(
                          (weakness, idx) => (
                            <li
                              key={idx}
                              className="text-sm text-muted-foreground flex items-start gap-2"
                            >
                              <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                              {weakness}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
          </div>

          {/* Reset Button */}
          <button
            onClick={() => {
              setResult(null);
              setDeals([
                { id: "1", companyName: "", file: null },
                { id: "2", companyName: "", file: null },
              ]);
            }}
            className="button-secondary w-full"
          >
            Compare New Deals
          </button>
        </div>
      )}
    </div>
  );
}
