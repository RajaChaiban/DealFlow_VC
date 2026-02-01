"use client";

import { TrendingUp, TrendingDown, MinusCircle, AlertTriangle, Search } from "lucide-react";

interface RecommendationBadgeProps {
  recommendation: string;
  size?: "sm" | "md" | "lg";
}

const recommendationConfig: Record<
  string,
  { label: string; color: string; bg: string; border: string; icon: React.ElementType }
> = {
  strong_invest: {
    label: "Strong Invest",
    color: "text-emerald-400",
    bg: "bg-emerald-500/15",
    border: "border-emerald-500/30",
    icon: TrendingUp,
  },
  invest: {
    label: "Invest",
    color: "text-green-400",
    bg: "bg-green-500/15",
    border: "border-green-500/30",
    icon: TrendingUp,
  },
  conditional_invest: {
    label: "Conditional Invest",
    color: "text-blue-400",
    bg: "bg-blue-500/15",
    border: "border-blue-500/30",
    icon: MinusCircle,
  },
  more_diligence: {
    label: "More Diligence",
    color: "text-amber-400",
    bg: "bg-amber-500/15",
    border: "border-amber-500/30",
    icon: Search,
  },
  pass: {
    label: "Pass",
    color: "text-orange-400",
    bg: "bg-orange-500/15",
    border: "border-orange-500/30",
    icon: TrendingDown,
  },
  strong_pass: {
    label: "Strong Pass",
    color: "text-red-400",
    bg: "bg-red-500/15",
    border: "border-red-500/30",
    icon: AlertTriangle,
  },
};

export default function RecommendationBadge({
  recommendation,
  size = "md",
}: RecommendationBadgeProps) {
  const config =
    recommendationConfig[recommendation] ||
    recommendationConfig["more_diligence"];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "px-2.5 py-1 text-xs gap-1.5",
    md: "px-3 py-1.5 text-sm gap-2",
    lg: "px-4 py-2 text-base gap-2.5",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-lg border ${config.bg} ${config.border} ${config.color} ${sizeClasses[size]}`}
    >
      <Icon className={iconSizes[size]} />
      {config.label}
    </span>
  );
}
