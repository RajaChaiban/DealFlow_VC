"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Upload,
  GitCompare,
  MessageSquare,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  BarChart3,
  PieChart,
  Activity,
} from "lucide-react";
import { Deal } from "@/types";
import { API_V1 } from "@/lib/utils";

interface DashboardStats {
  total_deals: number;
  in_progress: number;
  completed: number;
  avg_score: number;
}

interface PortfolioAnalytics {
  total_deals_analyzed: number;
  average_score: number;
  score_distribution: Record<string, number>;
  recommendation_breakdown: Record<string, number>;
  industry_breakdown: Record<string, number>;
  pipeline: {
    total_deals: number;
    active_deals: number;
    stage_distribution: Record<string, number>;
    priority_distribution: Record<string, number>;
    avg_diligence_completion: number;
    conversion_rate: number;
  };
  monthly_volume: { month: string; count: number }[];
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_deals: 0,
    in_progress: 0,
    completed: 0,
    avg_score: 0,
  });
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [pipelineCounts, setPipelineCounts] = useState<Record<string, number>>(
    {}
  );
  const [analytics, setAnalytics] = useState<PortfolioAnalytics | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      const [dealsRes, pipelineRes, analyticsRes] = await Promise.allSettled([
        fetch(`${API_V1}/deals`),
        fetch(`${API_V1}/pipeline/`),
        fetch(`${API_V1}/analytics/portfolio`),
      ]);

      // Parse deals response: backend returns { total, analyses: [...] }
      let deals: Deal[] = [];
      if (dealsRes.status === "fulfilled" && dealsRes.value.ok) {
        const dealsData = await dealsRes.value.json();
        deals = (dealsData.analyses || []).map((a: any) => ({
          id: a.analysis_id || a.id,
          analysis_id: a.analysis_id,
          company_name: a.company_name || "Unknown",
          status: a.status || "pending",
          overall_score: a.overall_score || 0,
          recommendation: a.recommendation || "",
          created_at: a.started_at || a.created_at || new Date().toISOString(),
          has_result: a.has_result || false,
        }));
      }

      // Parse pipeline response
      if (pipelineRes.status === "fulfilled" && pipelineRes.value.ok) {
        const pipelineData = await pipelineRes.value.json();
        setPipelineCounts(pipelineData.counts || {});
      }

      // Parse analytics response
      if (analyticsRes.status === "fulfilled" && analyticsRes.value.ok) {
        const analyticsData = await analyticsRes.value.json();
        setAnalytics(analyticsData);
      }

      // Calculate stats
      const completed = deals.filter((d) => d.status === "completed").length;
      const inProgress = deals.filter(
        (d) => d.status === "running" || d.status === "processing"
      ).length;
      const avgScore =
        deals.length > 0
          ? deals.reduce((sum, d) => sum + (d.overall_score || 0), 0) /
            deals.length
          : 0;

      setStats({
        total_deals: deals.length,
        in_progress: inProgress,
        completed: completed,
        avg_score: Math.round(avgScore * 10) / 10,
      });

      setRecentDeals(deals.slice(0, 5));
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: "Total Deals Analyzed",
      value: analytics?.total_deals_analyzed ?? stats.total_deals,
      icon: BarChart3,
      color: "text-blue-400",
      bgColor: "bg-blue-500/20",
      borderColor: "border-blue-500/30",
    },
    {
      title: "Active Pipeline",
      value: analytics?.pipeline?.active_deals ?? stats.in_progress,
      icon: Clock,
      color: "text-amber-400",
      bgColor: "bg-amber-500/20",
      borderColor: "border-amber-500/30",
    },
    {
      title: "Avg Score",
      value: analytics?.average_score ?? stats.avg_score,
      icon: TrendingUp,
      color: "text-purple-400",
      bgColor: "bg-purple-500/20",
      borderColor: "border-purple-500/30",
      suffix: "/10",
    },
    {
      title: "Conversion Rate",
      value: analytics?.pipeline?.conversion_rate
        ? `${Math.round(analytics.pipeline.conversion_rate)}%`
        : "0%",
      icon: CheckCircle2,
      color: "text-green-400",
      bgColor: "bg-green-500/20",
      borderColor: "border-green-500/30",
    },
  ];

  const quickActions = [
    {
      title: "Upload New Deck",
      description: "Analyze a new deal opportunity",
      icon: Upload,
      href: "/deals",
      color: "bg-primary hover:bg-primary/90",
    },
    {
      title: "Compare Deals",
      description: "Side-by-side comparison",
      icon: GitCompare,
      href: "/compare",
      color: "bg-secondary hover:bg-secondary/80",
    },
    {
      title: "Chat with AI",
      description: "Ask questions about deals",
      icon: MessageSquare,
      href: "/chat",
      color: "bg-secondary hover:bg-secondary/80",
    },
  ];

  const getRecommendationBadge = (recommendation: string) => {
    const classes: Record<string, string> = {
      "Strong Buy": "badge-success",
      Buy: "badge-success",
      Hold: "badge-warning",
      Pass: "badge-danger",
      "Strong Pass": "badge-danger",
    };
    return classes[recommendation] || "badge-info";
  };

  const recColors: Record<string, string> = {
    "Strong Buy": "bg-emerald-500",
    Buy: "bg-green-500",
    Hold: "bg-amber-500",
    Pass: "bg-orange-500",
    "Strong Pass": "bg-red-500",
    Unknown: "bg-gray-500",
  };

  const pipelineStages = [
    { stage: "New", key: "new", color: "bg-blue-500" },
    { stage: "Screening", key: "screening", color: "bg-purple-500" },
    { stage: "Diligence", key: "diligence", color: "bg-amber-500" },
    { stage: "IC Review", key: "ic_review", color: "bg-orange-500" },
    { stage: "Term Sheet", key: "term_sheet", color: "bg-green-500" },
    { stage: "Closed", key: "closed_won", color: "bg-emerald-500" },
  ];

  // Helpers for chart rendering
  const scoreDistMax = analytics
    ? Math.max(...Object.values(analytics.score_distribution), 1)
    : 1;

  const recTotal = analytics
    ? Object.values(analytics.recommendation_breakdown).reduce(
        (a, b) => a + b,
        0
      )
    : 0;

  const monthlyMax = analytics
    ? Math.max(...analytics.monthly_volume.map((m) => m.count), 1)
    : 1;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="mt-2 text-muted-foreground">
          Welcome back to your deal analysis platform
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div
            key={stat.title}
            className={`glass-effect rounded-lg border p-6 card-hover ${stat.borderColor}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </p>
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {loading ? (
                    <span className="skeleton h-10 w-20 inline-block" />
                  ) : (
                    <>
                      {stat.value}
                      {stat.suffix && (
                        <span className="text-lg text-muted-foreground">
                          {stat.suffix}
                        </span>
                      )}
                    </>
                  )}
                </p>
              </div>
              <div className={`rounded-full p-3 ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="mb-4 text-xl font-semibold text-foreground">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {quickActions.map((action) => (
            <Link
              key={action.title}
              href={action.href}
              className={`glass-effect group rounded-lg border border-border p-6 transition-all hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1 ${action.color}`}
            >
              <div className="flex items-center gap-4">
                <div className="rounded-lg bg-white/10 p-3">
                  <action.icon className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">{action.title}</h3>
                  <p className="mt-1 text-sm text-white/80">
                    {action.description}
                  </p>
                </div>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Analytics Charts Row */}
      {analytics && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Score Distribution */}
          <div className="glass-effect rounded-lg border border-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold text-foreground">
                Score Distribution
              </h3>
            </div>
            <div className="space-y-3">
              {Object.entries(analytics.score_distribution).map(
                ([bucket, count]) => (
                  <div key={bucket} className="flex items-center gap-3">
                    <span className="w-12 text-sm text-muted-foreground text-right">
                      {bucket}
                    </span>
                    <div className="flex-1 h-6 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-500"
                        style={{
                          width: `${(count / scoreDistMax) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="w-8 text-sm font-medium text-foreground">
                      {count}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Recommendation Breakdown */}
          <div className="glass-effect rounded-lg border border-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <PieChart className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold text-foreground">
                Recommendations
              </h3>
            </div>
            {recTotal === 0 ? (
              <p className="text-sm text-muted-foreground">
                No completed analyses yet
              </p>
            ) : (
              <div className="space-y-3">
                {Object.entries(analytics.recommendation_breakdown).map(
                  ([rec, count]) => (
                    <div key={rec} className="flex items-center gap-3">
                      <span className="w-24 text-sm text-muted-foreground truncate">
                        {rec}
                      </span>
                      <div className="flex-1 h-6 bg-secondary rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            recColors[rec] || "bg-gray-500"
                          }`}
                          style={{
                            width: `${(count / recTotal) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="w-8 text-sm font-medium text-foreground">
                        {count}
                      </span>
                    </div>
                  )
                )}
              </div>
            )}
          </div>

          {/* Monthly Volume */}
          {analytics.monthly_volume.length > 0 && (
            <div className="glass-effect rounded-lg border border-border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">
                  Monthly Deal Volume
                </h3>
              </div>
              <div className="flex items-end gap-2 h-32">
                {analytics.monthly_volume.map((m) => (
                  <div
                    key={m.month}
                    className="flex-1 flex flex-col items-center gap-1"
                  >
                    <span className="text-xs font-medium text-foreground">
                      {m.count}
                    </span>
                    <div
                      className="w-full bg-primary/80 rounded-t transition-all duration-500"
                      style={{
                        height: `${(m.count / monthlyMax) * 100}%`,
                        minHeight: m.count > 0 ? "8px" : "2px",
                      }}
                    />
                    <span className="text-xs text-muted-foreground">
                      {m.month.slice(5)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Industry Breakdown */}
          {Object.keys(analytics.industry_breakdown).length > 0 && (
            <div className="glass-effect rounded-lg border border-border p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">
                  Industry Breakdown
                </h3>
              </div>
              <div className="space-y-2">
                {Object.entries(analytics.industry_breakdown)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 6)
                  .map(([industry, count]) => {
                    const indMax = Math.max(
                      ...Object.values(analytics.industry_breakdown)
                    );
                    return (
                      <div key={industry} className="flex items-center gap-3">
                        <span className="w-28 text-sm text-muted-foreground truncate">
                          {industry}
                        </span>
                        <div className="flex-1 h-5 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full transition-all duration-500"
                            style={{
                              width: `${(count / indMax) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="w-6 text-sm font-medium text-foreground">
                          {count}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Analyses */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-foreground">
            Recent Analyses
          </h2>
          <Link
            href="/pipeline"
            className="text-sm text-primary hover:text-primary/80 flex items-center gap-1"
          >
            View All
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="glass-effect rounded-lg border border-border p-6"
              >
                <div className="skeleton h-6 w-48 mb-3" />
                <div className="skeleton h-4 w-full" />
              </div>
            ))}
          </div>
        ) : recentDeals.length === 0 ? (
          <div className="glass-effect rounded-lg border border-border p-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">
              No deals yet
            </h3>
            <p className="text-muted-foreground mb-6">
              Get started by uploading your first deal deck
            </p>
            <Link href="/deals" className="button-primary inline-block">
              Upload Deal
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recentDeals.map((deal) => (
              <div
                key={deal.id}
                className="glass-effect block rounded-lg border border-border p-6 card-hover"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-foreground">
                        {deal.company_name}
                      </h3>
                      {deal.recommendation && (
                        <span
                          className={`badge ${getRecommendationBadge(
                            deal.recommendation
                          )}`}
                        >
                          {deal.recommendation}
                        </span>
                      )}
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {new Date(deal.created_at).toLocaleDateString()}
                      </span>
                      {deal.overall_score > 0 && (
                        <span>Score: {deal.overall_score}/10</span>
                      )}
                      <span className="capitalize">{deal.status}</span>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pipeline Overview Mini Chart */}
      <div className="glass-effect rounded-lg border border-border p-6">
        <h2 className="mb-4 text-xl font-semibold text-foreground">
          Pipeline Overview
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {pipelineStages.map((stage) => (
            <div key={stage.key} className="text-center">
              <div
                className={`mx-auto mb-2 h-16 w-16 rounded-full ${stage.color}/20 flex items-center justify-center`}
              >
                <span className="text-2xl font-bold text-foreground">
                  {pipelineCounts[stage.key] || 0}
                </span>
              </div>
              <p className="text-sm font-medium text-muted-foreground">
                {stage.stage}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
