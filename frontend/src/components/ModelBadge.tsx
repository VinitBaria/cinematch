import React from 'react';
import { Cpu, Sparkles, TrendingUp } from 'lucide-react';

interface ModelBadgeProps {
  strategy?: string;
  predictedRating?: number;
  className?: string;
}

export const ModelBadge: React.FC<ModelBadgeProps> = ({
  strategy = 'svd_matrix_factorization',
  predictedRating,
  className = '',
}) => {
  if (strategy === 'svd_matrix_factorization' || strategy === 'svd') {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-950/70 text-red-300 border border-red-800/60 shadow-sm ${className}`}>
        <Sparkles className="w-3.5 h-3.5 text-red-400 animate-pulse" />
        <span>SVD Collaborative Filtering</span>
        {predictedRating !== undefined && (
          <span className="ml-1 px-1.5 py-0.5 rounded bg-red-900 text-white font-mono text-[11px]">
            {predictedRating.toFixed(2)}★
          </span>
        )}
      </div>
    );
  }

  if (strategy === 'neighbor_collaborative_filtering' || strategy === 'collaborative_filtering') {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-800/60 shadow-sm ${className}`}>
        <Cpu className="w-3.5 h-3.5 text-emerald-400" />
        <span>Neighbor CF</span>
        {predictedRating !== undefined && (
          <span className="ml-1 px-1.5 py-0.5 rounded bg-emerald-900 text-white font-mono text-[11px]">
            {predictedRating.toFixed(2)}★
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/70 text-amber-300 border border-amber-800/60 shadow-sm ${className}`}>
      <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
      <span>Popularity Weighted</span>
    </div>
  );
};
