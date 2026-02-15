import { ReactNode } from "react";

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function Card({ title, children, className = "" }: CardProps) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      {title && (
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
