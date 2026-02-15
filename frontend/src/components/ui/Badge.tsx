const colorMap: Record<string, string> = {
  blue: "bg-blue-100 text-blue-800",
  green: "bg-green-100 text-green-800",
  yellow: "bg-yellow-100 text-yellow-800",
  red: "bg-red-100 text-red-800",
  gray: "bg-gray-100 text-gray-700",
  indigo: "bg-indigo-100 text-indigo-800",
  cyan: "bg-cyan-100 text-cyan-800",
  orange: "bg-orange-100 text-orange-800",
};

interface BadgeProps {
  label: string;
  color?: keyof typeof colorMap;
  className?: string;
}

export default function Badge({ label, color = "gray", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorMap[color] || colorMap.gray} ${className}`}
    >
      {label}
    </span>
  );
}

// Helpers for common badge types
export function TierBadge({ tier }: { tier: string }) {
  const color = tier === "Whale" ? "indigo" : tier === "Tuna" ? "blue" : tier === "Infra" ? "gray" : "cyan";
  return <Badge label={tier} color={color} />;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const color = severity === "red" ? "red" : severity === "yellow" ? "yellow" : "green";
  return <Badge label={severity} color={color} />;
}

export function ReadinessBadge({ readiness }: { readiness: string }) {
  const color = readiness === "high" ? "green" : readiness === "medium" ? "yellow" : "gray";
  return <Badge label={readiness} color={color} />;
}
