import React from 'react';
import { Play, Info, Star, Sparkles } from 'lucide-react';
import { StarRating } from './StarRating';
import { Poster } from './Poster';
import {
  AnyMovie,
  displayTitle,
  displayYear,
  isRecommendation,
  matchPercent,
} from '../utils/movie';
import { Movie } from '../types';

interface MovieCardProps {
  movie: AnyMovie;
  onSelect: (movie: AnyMovie) => void;
  onRate?: (movieId: number, rating: number) => void;
  userRating?: number;
  /** Fill the parent (grids). Default is a fixed width for carousels. */
  fluid?: boolean;
  /** Stagger index for entrance animation in grids. */
  index?: number;
}

export const MovieCard: React.FC<MovieCardProps> = ({
  movie,
  onSelect,
  onRate,
  userRating,
  fluid = false,
  index,
}) => {
  const rec = isRecommendation(movie);
  const match = matchPercent(movie);
  const rated = userRating || (movie as Movie).userRating;
  const title = displayTitle(movie);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${title}${displayYear(movie) ? `, ${displayYear(movie)}` : ''}. Open details`}
      onClick={() => onSelect(movie)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(movie);
        }
      }}
      style={index !== undefined ? { animationDelay: `${Math.min(index, 18) * 40}ms` } : undefined}
      className={`group relative aspect-[2/3] cursor-pointer rounded-md bg-[#1c1c1c]
        shadow-lg shadow-black/40 ring-1 ring-white/5
        transition-[transform,box-shadow] duration-300 ease-out will-change-transform
        hover:z-30 hover:scale-[1.12] hover:shadow-2xl hover:shadow-black/80 hover:ring-white/20
        focus-visible:z-30 focus-visible:scale-[1.08]
        ${fluid ? 'w-full' : 'w-[140px] flex-none sm:w-[170px] md:w-[200px] lg:w-[220px]'}
        ${index !== undefined ? 'animate-fade-up' : ''}`}
    >
      <Poster movie={movie} className="absolute inset-0 rounded-md" />

      {/* Always-on bottom title (so touch users can read it) */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 rounded-b-md bg-gradient-to-t from-black/90 via-black/40 to-transparent px-2.5 pb-2 pt-10 transition-opacity duration-200 group-hover:opacity-0 group-focus-visible:opacity-0">
        <p className="line-clamp-1 text-xs font-bold text-white drop-shadow">{title}</p>
      </div>

      {/* Corner badges */}
      <div className="pointer-events-none absolute left-2 top-2 flex flex-col items-start gap-1">
        {rec && (
          <span className="inline-flex items-center gap-1 rounded bg-[#e50914] px-1.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-white shadow">
            <Sparkles className="h-2.5 w-2.5" /> AI Pick
          </span>
        )}
      </div>
      {rated ? (
        <div className="pointer-events-none absolute right-2 top-2 flex items-center gap-0.5 rounded bg-amber-400 px-1.5 py-0.5 text-[11px] font-black text-black shadow">
          <Star className="h-3 w-3 fill-black" />
          {rated}
        </div>
      ) : null}

      {/* Hover panel */}
      <div
        className="absolute inset-x-0 bottom-0 translate-y-3 rounded-b-md bg-gradient-to-t from-[#101010] via-[#101010]/95 to-transparent
          px-3 pb-3 pt-14 opacity-0 transition-all duration-300 ease-out
          group-hover:translate-y-0 group-hover:opacity-100
          group-focus-visible:translate-y-0 group-focus-visible:opacity-100"
      >
        <div className="mb-2 flex items-center gap-2">
          <span
            aria-hidden
            className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-black shadow transition-transform hover:scale-110"
          >
            <Play className="ml-0.5 h-4 w-4 fill-black" />
          </span>
          <span
            aria-hidden
            className="ml-auto flex h-8 w-8 items-center justify-center rounded-full border border-white/40 bg-black/50 text-white transition-colors hover:border-white"
          >
            <Info className="h-4 w-4" />
          </span>
        </div>

        <p className="line-clamp-2 text-[13px] font-bold leading-tight text-white">{title}</p>

        <div className="mt-1 flex flex-wrap items-center gap-x-2 text-[11px] font-semibold">
          {match && <span className="text-emerald-400">{match}% Match</span>}
          {displayYear(movie) && <span className="text-zinc-300">{displayYear(movie)}</span>}
          {movie.avgRating ? (
            <span className="flex items-center gap-0.5 text-amber-400">
              <Star className="h-3 w-3 fill-amber-400" /> {movie.avgRating.toFixed(1)}
            </span>
          ) : null}
        </div>

        {movie.genres?.length > 0 && (
          <p className="mt-1 line-clamp-1 text-[10px] text-zinc-400">
            {movie.genres.slice(0, 3).join(' • ')}
          </p>
        )}

        {onRate && (
          <div className="mt-2 border-t border-white/10 pt-2" onClick={(e) => e.stopPropagation()}>
            <StarRating
              rating={rated || 0}
              size="sm"
              showValue={false}
              onRate={(r) => onRate(movie.movieId, r)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export const MovieCardSkeleton: React.FC<{ fluid?: boolean }> = ({ fluid = false }) => (
  <div
    className={`aspect-[2/3] rounded-md skeleton ${
      fluid ? 'w-full' : 'w-[140px] flex-none sm:w-[170px] md:w-[200px] lg:w-[220px]'
    }`}
  />
);
