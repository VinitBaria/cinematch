import React, { useState } from 'react';
import { Film } from 'lucide-react';
import { AnyMovie, displayTitle, displayYear, posterGradient } from '../utils/movie';

interface PosterProps {
  movie: AnyMovie;
  className?: string;
  imgClassName?: string;
  eager?: boolean;
  /** Show the title on the placeholder when artwork is missing. */
  showFallbackTitle?: boolean;
}

/** Poster with a blur-up fade-in and a designed fallback when artwork is missing/broken. */
export const Poster: React.FC<PosterProps> = ({
  movie,
  className = '',
  imgClassName = '',
  eager = false,
  showFallbackTitle = true,
}) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const hasImage = !!movie.posterUrl && !error;
  const title = displayTitle(movie);

  return (
    <div className={`relative overflow-hidden bg-[#1c1c1c] ${className}`}>
      {hasImage ? (
        <>
          {!loaded && <div className="absolute inset-0 skeleton" />}
          <img
            src={movie.posterUrl}
            alt={title}
            loading={eager ? 'eager' : 'lazy'}
            decoding="async"
            referrerPolicy="no-referrer"
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
            className={`h-full w-full object-cover transition-all duration-700 ${
              loaded ? 'opacity-100 blur-0 scale-100' : 'opacity-0 blur-md scale-105'
            } ${imgClassName}`}
          />
        </>
      ) : (
        <div
          className="absolute inset-0 flex flex-col items-center justify-between p-4 text-center"
          style={{ background: posterGradient(title) }}
        >
          <Film className="h-5 w-5 text-white/30" />
          {showFallbackTitle && (
            <div>
              <p className="line-clamp-4 text-sm font-extrabold leading-tight text-white drop-shadow">
                {title}
              </p>
              {displayYear(movie) && (
                <p className="mt-1 text-[11px] font-semibold text-white/50">{displayYear(movie)}</p>
              )}
            </div>
          )}
          <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">
            {movie.genres?.[0] ?? 'Feature'}
          </span>
        </div>
      )}
    </div>
  );
};
