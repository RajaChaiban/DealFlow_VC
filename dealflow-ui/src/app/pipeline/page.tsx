"use client";

import { useEffect, useState } from "react";
import {
  GripVertical,
  Plus,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Filter,
} from "lucide-react";
import { PipelineDeal } from "@/types";
import { API_V1 } from "@/lib/utils";

interface PipelineStageConfig {
  id: string;
  name: string;
  color: string;
}

const STAGE_CONFIGS: PipelineStageConfig[] = [
  { id: "new", name: "New", color: "bg-blue-500" },
  { id: "screening", name: "Screening", color: "bg-purple-500" },
  { id: "diligence", name: "Diligence", color: "bg-amber-500" },
  { id: "ic_review", name: "IC Review", color: "bg-orange-500" },
  { id: "term_sheet", name: "Term Sheet", color: "bg-green-500" },
  { id: "closed_won", name: "Closed Won", color: "bg-emerald-500" },
  { id: "closed_lost", name: "Closed Lost", color: "bg-gray-500" },
  { id: "passed", name: "Passed", color: "bg-red-500" },
];

export default function PipelinePage() {
  const [board, setBoard] = useState<Record<string, PipelineDeal[]>>({});
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [totalDeals, setTotalDeals] = useState(0);
  const [activeDeals, setActiveDeals] = useState(0);
  const [loading, setLoading] = useState(true);
  const [draggedDeal, setDraggedDeal] = useState<PipelineDeal | null>(null);
  const [dragSourceStage, setDragSourceStage] = useState<string | null>(null);

  useEffect(() => {
    fetchPipelineData();
  }, []);

  const fetchPipelineData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_V1}/pipeline/`);
      if (!response.ok) throw new Error("Failed to fetch pipeline");

      const data = await response.json();
      setBoard(data.board || {});
      setCounts(data.counts || {});
      setTotalDeals(data.total_deals || 0);
      setActiveDeals(data.active_deals || 0);
    } catch (error) {
      console.error("Failed to fetch pipeline data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (deal: PipelineDeal, stageId: string) => {
    setDraggedDeal(deal);
    setDragSourceStage(stageId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (targetStageId: string) => {
    if (!draggedDeal || !dragSourceStage || dragSourceStage === targetStageId) {
      setDraggedDeal(null);
      setDragSourceStage(null);
      return;
    }

    const entryId = draggedDeal.analysis_id;

    // Optimistic UI update
    const newBoard = { ...board };
    newBoard[dragSourceStage] = (newBoard[dragSourceStage] || []).filter(
      (d) => d.analysis_id !== entryId
    );
    newBoard[targetStageId] = [
      ...(newBoard[targetStageId] || []),
      { ...draggedDeal, stage: targetStageId },
    ];
    setBoard(newBoard);

    // Update counts
    const newCounts = { ...counts };
    newCounts[dragSourceStage] = (newCounts[dragSourceStage] || 1) - 1;
    newCounts[targetStageId] = (newCounts[targetStageId] || 0) + 1;
    setCounts(newCounts);

    try {
      const response = await fetch(`${API_V1}/pipeline/${entryId}/stage`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_stage: targetStageId }),
      });

      if (!response.ok) {
        // Revert on failure
        fetchPipelineData();
      }
    } catch (error) {
      console.error("Failed to update deal stage:", error);
      fetchPipelineData();
    } finally {
      setDraggedDeal(null);
      setDragSourceStage(null);
    }
  };

  const getPriorityBadge = (priority: string) => {
    const badges: Record<string, { label: string; class: string }> = {
      urgent: { label: "Urgent", class: "badge-danger" },
      high: { label: "High", class: "badge-warning" },
      medium: { label: "Medium", class: "badge-info" },
      low: { label: "Low", class: "badge-success" },
    };
    return badges[priority] || { label: priority, class: "badge-info" };
  };

  const getStageIcon = (stageId: string) => {
    const icons: Record<string, any> = {
      new: Plus,
      screening: Filter,
      diligence: AlertCircle,
      ic_review: TrendingUp,
      term_sheet: CheckCircle2,
      closed_won: CheckCircle2,
      closed_lost: XCircle,
      passed: XCircle,
    };
    return icons[stageId] || Clock;
  };

  const getStageDeals = (stageId: string): PipelineDeal[] => {
    return board[stageId] || [];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Deal Pipeline</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your deals through the investment process
          </p>
        </div>
      </div>

      {/* Pipeline Stages */}
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-4 min-w-max">
          {STAGE_CONFIGS.map((stage) => {
            const StageIcon = getStageIcon(stage.id);
            const stageDeals = getStageDeals(stage.id);
            return (
              <div
                key={stage.id}
                onDragOver={handleDragOver}
                onDrop={() => handleDrop(stage.id)}
                className="glass-effect flex-shrink-0 w-80 rounded-lg border border-border"
              >
                {/* Stage Header */}
                <div className={`${stage.color}/20 border-b border-border p-4`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`rounded-lg ${stage.color}/30 p-2`}>
                        <StageIcon className="h-4 w-4 text-white" />
                      </div>
                      <h3 className="font-semibold text-foreground">
                        {stage.name}
                      </h3>
                    </div>
                    <span
                      className={`flex h-6 w-6 items-center justify-center rounded-full ${stage.color}/30 text-xs font-bold text-white`}
                    >
                      {counts[stage.id] || 0}
                    </span>
                  </div>
                </div>

                {/* Stage Content */}
                <div className="p-3 space-y-3 min-h-[600px] max-h-[600px] overflow-y-auto">
                  {loading ? (
                    [...Array(2)].map((_, i) => (
                      <div key={i} className="skeleton h-32 rounded-lg" />
                    ))
                  ) : stageDeals.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <div className="rounded-full bg-muted p-3 mb-3">
                        <StageIcon className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        No deals in this stage
                      </p>
                    </div>
                  ) : (
                    stageDeals.map((deal) => {
                      const priority = getPriorityBadge(deal.priority || "medium");
                      return (
                        <div
                          key={deal.analysis_id}
                          draggable
                          onDragStart={() => handleDragStart(deal, stage.id)}
                          className="glass-effect group cursor-move rounded-lg border border-border p-4 card-hover"
                        >
                          <div className="flex items-start gap-3">
                            <GripVertical className="h-5 w-5 flex-shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-foreground truncate mb-2">
                                {deal.company_name}
                              </h4>

                              <div className="flex items-center gap-2 mb-3">
                                <span className={`badge ${priority.class}`}>
                                  {priority.label}
                                </span>
                                {deal.assigned_to && (
                                  <span className="text-xs text-muted-foreground">
                                    {deal.assigned_to}
                                  </span>
                                )}
                              </div>

                              {/* Tags */}
                              {deal.tags && deal.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-3">
                                  {deal.tags.map((tag, idx) => (
                                    <span
                                      key={idx}
                                      className="text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {/* Diligence Progress */}
                              {deal.diligence_checklist && deal.diligence_checklist.length > 0 && (
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between text-xs">
                                    <span className="text-muted-foreground">
                                      Diligence
                                    </span>
                                    <span className="font-medium text-foreground">
                                      {Math.round(deal.diligence_completion_pct || 0)}%
                                    </span>
                                  </div>
                                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                    <div
                                      className={`h-full ${stage.color} transition-all`}
                                      style={{
                                        width: `${deal.diligence_completion_pct || 0}%`,
                                      }}
                                    />
                                  </div>
                                </div>
                              )}

                              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span>
                                  {new Date(deal.created_at).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pipeline Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-effect rounded-lg border border-border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Deals</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {totalDeals}
              </p>
            </div>
            <div className="rounded-full bg-blue-500/20 p-3">
              <TrendingUp className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </div>

        <div className="glass-effect rounded-lg border border-border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {activeDeals}
              </p>
            </div>
            <div className="rounded-full bg-purple-500/20 p-3">
              <Clock className="h-6 w-6 text-purple-400" />
            </div>
          </div>
        </div>

        <div className="glass-effect rounded-lg border border-border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Won</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {counts["closed_won"] || 0}
              </p>
            </div>
            <div className="rounded-full bg-green-500/20 p-3">
              <CheckCircle2 className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </div>

        <div className="glass-effect rounded-lg border border-border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Passed</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {counts["passed"] || 0}
              </p>
            </div>
            <div className="rounded-full bg-red-500/20 p-3">
              <XCircle className="h-6 w-6 text-red-400" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
