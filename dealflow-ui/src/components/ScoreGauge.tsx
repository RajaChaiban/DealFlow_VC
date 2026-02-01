"use client";

interface ScoreGaugeProps {
  score: number;
  maxScore?: number;
  label: string;
  size?: "sm" | "md" | "lg";
}

export default function ScoreGauge({
  score,
  maxScore = 10,
  label,
  size = "md",
}: ScoreGaugeProps) {
  const percentage = (score / maxScore) * 100;

  const getColor = (pct: number) => {
    if (pct >= 70) return { stroke: "#10b981", text: "text-emerald-400" };
    if (pct >= 40) return { stroke: "#f59e0b", text: "text-amber-400" };
    return { stroke: "#ef4444", text: "text-red-400" };
  };

  const color = getColor(percentage);

  const sizes = {
    sm: { dim: 64, strokeWidth: 4, fontSize: "text-sm" },
    md: { dim: 80, strokeWidth: 5, fontSize: "text-lg" },
    lg: { dim: 100, strokeWidth: 6, fontSize: "text-xl" },
  };

  const { dim, strokeWidth, fontSize } = sizes[size];
  const radius = (dim - strokeWidth * 2) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: dim, height: dim }}>
        <svg
          width={dim}
          height={dim}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            fill="none"
            stroke="#1e293b"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            fill="none"
            stroke={color.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`font-bold ${fontSize} ${color.text}`}>
            {score.toFixed(1)}
          </span>
        </div>
      </div>
      <span className="text-xs text-slate-400 font-medium text-center">
        {label}
      </span>
    </div>
  );
}
