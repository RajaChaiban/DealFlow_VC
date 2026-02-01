"use client";

import { Check, Loader2, FileSearch, BarChart3, Shield, DollarSign, FileText } from "lucide-react";

interface Step {
  name: string;
  description: string;
  icon: React.ElementType;
  status: "pending" | "active" | "completed" | "failed";
}

interface AnalysisProgressProps {
  currentStep: number;
  steps?: Step[];
}

const defaultSteps: Step[] = [
  {
    name: "Extracting Data",
    description: "Reading pitch deck with AI vision",
    icon: FileSearch,
    status: "pending",
  },
  {
    name: "Business Analysis",
    description: "Evaluating business model & market",
    icon: BarChart3,
    status: "pending",
  },
  {
    name: "Risk Assessment",
    description: "Identifying risks & red flags",
    icon: Shield,
    status: "pending",
  },
  {
    name: "Valuation",
    description: "Running valuation methodologies",
    icon: DollarSign,
    status: "pending",
  },
  {
    name: "IC Memo",
    description: "Generating investment memo",
    icon: FileText,
    status: "pending",
  },
];

export default function AnalysisProgress({
  currentStep,
  steps,
}: AnalysisProgressProps) {
  const activeSteps = (steps || defaultSteps).map((step, index) => ({
    ...step,
    status:
      index < currentStep
        ? ("completed" as const)
        : index === currentStep
        ? ("active" as const)
        : ("pending" as const),
  }));

  const progress = ((currentStep + 1) / activeSteps.length) * 100;

  return (
    <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-6">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-slate-300">
            Analyzing Deal...
          </span>
          <span className="text-sm text-blue-400">{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {activeSteps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div
              key={index}
              className={`flex items-center gap-4 p-3 rounded-lg transition-all ${
                step.status === "active"
                  ? "bg-blue-500/10 border border-blue-500/30"
                  : step.status === "completed"
                  ? "bg-emerald-500/5 border border-emerald-500/20"
                  : "bg-slate-800/30 border border-transparent"
              }`}
            >
              {/* Status Icon */}
              <div
                className={`h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  step.status === "completed"
                    ? "bg-emerald-500/20"
                    : step.status === "active"
                    ? "bg-blue-500/20"
                    : "bg-slate-800"
                }`}
              >
                {step.status === "completed" ? (
                  <Check className="h-5 w-5 text-emerald-400" />
                ) : step.status === "active" ? (
                  <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                ) : (
                  <Icon className="h-5 w-5 text-slate-500" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm font-medium ${
                    step.status === "completed"
                      ? "text-emerald-400"
                      : step.status === "active"
                      ? "text-blue-400"
                      : "text-slate-500"
                  }`}
                >
                  {step.name}
                </p>
                <p className="text-xs text-slate-500 truncate">
                  {step.description}
                </p>
              </div>

              {/* Status Badge */}
              {step.status === "completed" && (
                <span className="text-xs text-emerald-400 font-medium">Done</span>
              )}
              {step.status === "active" && (
                <span className="text-xs text-blue-400 font-medium animate-pulse">
                  Running
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
