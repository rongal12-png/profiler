interface ProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  label?: string;
  showPct?: boolean;
  className?: string;
}

export default function ProgressBar({
  value,
  max = 100,
  color = "bg-blue-500",
  label,
  showPct = false,
  className = "",
}: ProgressBarProps) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;

  return (
    <div className={className}>
      {(label || showPct) && (
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          {label && <span>{label}</span>}
          {showPct && <span>{pct.toFixed(1)}%</span>}
        </div>
      )}
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
