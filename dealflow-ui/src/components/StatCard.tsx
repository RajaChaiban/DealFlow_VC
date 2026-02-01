"use client";

import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  color?: "blue" | "green" | "amber" | "red" | "purple";
}

const colorMap = {
  blue: {
    bg: "bg-blue-500/10",
    icon: "text-blue-400",
    border: "border-blue-500/20",
    trend: "text-blue-400",
  },
  green: {
    bg: "bg-emerald-500/10",
    icon: "text-emerald-400",
    border: "border-emerald-500/20",
    trend: "text-emerald-400",
  },
  amber: {
    bg: "bg-amber-500/10",
    icon: "text-amber-400",
    border: "border-amber-500/20",
    trend: "text-amber-400",
  },
  red: {
    bg: "bg-red-500/10",
    icon: "text-red-400",
    border: "border-red-500/20",
    trend: "text-red-400",
  },
  purple: {
    bg: "bg-purple-500/10",
    icon: "text-purple-400",
    border: "border-purple-500/20",
    trend: "text-purple-400",
  },
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = "blue",
}: StatCardProps) {
  const colors = colorMap[color];

  return (
    <div
      className={`rounded-xl border ${colors.border} ${colors.bg} backdrop-blur-sm p-5`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div
          className={`h-12 w-12 rounded-lg ${colors.bg} flex items-center justify-center`}
        >
          <Icon className={`h-6 w-6 ${colors.icon}`} />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1">
          <span className={`text-sm font-medium ${colors.trend}`}>
            {trend.value > 0 ? "+" : ""}
            {trend.value}%
          </span>
          <span className="text-xs text-slate-500">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
