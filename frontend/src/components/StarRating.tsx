import React, { useState } from 'react';
import { Star } from 'lucide-react';
import { RATING_LABELS } from '../utils/movie';

interface StarRatingProps {
  rating: number; // 0 to 5
  onRate?: (rating: number) => void;
  size?: 'sm' | 'md' | 'lg';
  readOnly?: boolean;
  /** Show the numeric value or the hover label next to the stars. */
  showValue?: boolean;
  showLabel?: boolean;
}

const SIZES = { sm: 'h-4 w-4', md: 'h-5 w-5', lg: 'h-8 w-8' };

export const StarRating: React.FC<StarRatingProps> = ({
  rating,
  onRate,
  size = 'md',
  readOnly = false,
  showValue = true,
  showLabel = false,
}) => {
  const [hover, setHover] = useState<number | null>(null);
  const [popped, setPopped] = useState<number | null>(null);
  const current = hover ?? rating;

  const handleClick = (star: number) => {
    if (!onRate) return;
    setPopped(star);
    window.setTimeout(() => setPopped(null), 450);
    onRate(star);
  };

  return (
    <div className="flex items-center gap-1" role="radiogroup" aria-label="Rating">
      <div className="flex items-center" onMouseLeave={() => !readOnly && setHover(null)}>
        {[1, 2, 3, 4, 5].map((star) => {
          const filled = current >= star;
          return (
            <button
              key={star}
              type="button"
              role="radio"
              aria-checked={Math.round(rating) === star}
              aria-label={`${star} star${star > 1 ? 's' : ''}`}
              disabled={readOnly}
              onClick={(e) => {
                e.stopPropagation();
                handleClick(star);
              }}
              onMouseEnter={() => !readOnly && setHover(star)}
              onFocus={() => !readOnly && setHover(star)}
              onBlur={() => setHover(null)}
              className={`rounded p-0.5 transition-transform duration-150 ${
                readOnly ? 'cursor-default' : 'hover:scale-125 active:scale-95'
              } ${popped === star ? 'animate-pop' : ''}`}
            >
              <Star
                className={`${SIZES[size]} transition-all duration-200 ${
                  filled
                    ? 'fill-amber-400 text-amber-400 drop-shadow-[0_0_6px_rgba(251,191,36,0.55)]'
                    : 'fill-transparent text-zinc-600'
                }`}
              />
            </button>
          );
        })}
      </div>
      {showLabel && (
        <span className="ml-2 min-w-[5.5rem] text-sm font-semibold text-zinc-200">
          {current > 0 ? RATING_LABELS[Math.round(current)] : 'Rate this'}
        </span>
      )}
      {showValue && !showLabel && rating > 0 && (
        <span className="ml-1 text-xs font-semibold tabular-nums text-zinc-300">{rating.toFixed(1)}</span>
      )}
    </div>
  );
};
