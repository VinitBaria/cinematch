import React, { useCallback, useEffect, useRef, useState } from 'react';
import { X, Star, Sparkles, ExternalLink, Trash2, Play, Check } from 'lucide-react';
import { StarRating } from './StarRating';
import { ModelBadge } from './ModelBadge';
import { Poster } from './Poster';
import {
  AnyMovie,
  displayTitle,
  displayYear,
  isRecommendation,
  matchPercent,
} from '../utils/movie';
import { Movie, RecommendationItem } from '../types';

interface MovieModalProps {
  movie: AnyMovie | null;
  isOpen: boolean;
  onClose: () => void;
  onRate: (movieId: number, rating: number) => void;
  onDeleteRating?: (movieId: number) => void;
  userRating?: number;
}

const EXIT_MS = 220;

export const MovieModal: React.FC<MovieModalProps> = ({
  movie,
  isOpen,
  onClose,
  onRate,
  onDeleteRating,
  userRating,
}) => {
  const [closing, setClosing] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const lastFocused = useRef<HTMLElement | null>(null);

  const requestClose = useCallback(() => {
    setClosing(true);
    window.setTimeout(() => {
      setClosing(false);
      onClose();
    }, EXIT_MS);
  }, [onClose]);

  // Scroll lock, Escape, focus management
  useEffect(() => {
    if (!isOpen) return;
    lastFocused.current = document.activeElement as HTMLElement | null;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialogRef.current?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') requestClose();
      if (e.key === 'Tab' && dialogRef.current) {
        const f = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
        );
        if (!f.length) return;
        const first = f[0];
        const last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
      lastFocused.current?.focus?.();
    };
  }, [isOpen, requestClose]);

  if (!isOpen || !movie) return null;

  const rec = isRecommendation(movie);
  const predicted = rec ? (movie as RecommendationItem).predictedRating : undefined;
  const strategy = rec ? (movie as RecommendationItem).recommendationStrategy : 'general_catalog';
  const effective = userRating !== undefined ? userRating : (movie as Movie).userRating;
  const match = matchPercent(movie);
  const title = displayTitle(movie);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto px-3 py-6 sm:py-10 md:px-6"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      {/* Backdrop */}
      <div
        onClick={requestClose}
        className={`fixed inset-0 bg-black/80 backdrop-blur-sm ${
          closing ? 'animate-overlay-out' : 'animate-overlay-in'
        }`}
      />

      {/* Panel */}
      <div
        ref={dialogRef}
        tabIndex={-1}
        className={`relative z-10 w-full max-w-4xl overflow-hidden rounded-xl bg-[#181818] text-white shadow-2xl shadow-black outline-none ring-1 ring-white/10 ${
          closing ? 'animate-modal-out' : 'animate-modal-in'
        }`}
      >
        <button
          onClick={requestClose}
          aria-label="Close"
          className="absolute right-4 top-4 z-30 flex h-9 w-9 items-center justify-center rounded-full bg-[#181818]/90 text-white transition-all hover:scale-110 hover:bg-white hover:text-black"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="relative h-[300px] w-full overflow-hidden bg-black sm:h-[400px]">
          {movie.posterUrl ? (
            <img
              src={movie.posterUrl}
              alt=""
              referrerPolicy="no-referrer"
              className="absolute inset-0 h-full w-full scale-125 object-cover object-top blur-2xl saturate-150 brightness-[0.55] animate-kenburns"
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-red-950 via-zinc-900 to-black" />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-[#181818] via-[#181818]/30 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#181818]/80 via-transparent to-transparent" />

          <Poster
            movie={movie}
            eager
            className="absolute bottom-6 right-6 hidden aspect-[2/3] w-40 rounded-lg shadow-2xl shadow-black ring-1 ring-white/20 sm:block md:w-48"
          />

          <div className="absolute bottom-6 left-6 right-6 sm:right-56 md:right-64">
            <h2 className="font-display text-4xl leading-none tracking-wide drop-shadow-lg sm:text-6xl animate-fade-up">
              {title}
            </h2>
            <div className="mt-5 flex flex-wrap items-center gap-3 animate-fade-up" style={{ animationDelay: '100ms' }}>
              <button
                onClick={requestClose}
                className="flex items-center gap-2 rounded-md bg-white px-6 py-2 text-base font-bold text-black transition-all hover:bg-white/80 active:scale-95"
              >
                <Play className="h-5 w-5 fill-black" /> Play
              </button>
              <div className="flex items-center gap-1 rounded-full border border-white/30 bg-black/40 px-4 py-1.5 backdrop-blur">
                <StarRating
                  rating={effective || 0}
                  size="md"
                  showValue={false}
                  onRate={(r) => onRate(movie.movieId, r)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="grid gap-8 px-6 pb-8 pt-2 sm:px-10 md:grid-cols-[1fr_260px]">
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold">
              {match && <span className="text-base font-bold text-emerald-400">{match}% Match</span>}
              {displayYear(movie) && <span className="text-zinc-300">{displayYear(movie)}</span>}
              {movie.avgRating ? (
                <span className="flex items-center gap-1 text-amber-400">
                  <Star className="h-4 w-4 fill-amber-400" />
                  {movie.avgRating.toFixed(1)}
                  {movie.ratingCount ? (
                    <span className="font-normal text-zinc-500">({movie.ratingCount.toLocaleString()})</span>
                  ) : null}
                </span>
              ) : null}
            </div>

            {rec && (
              <div className="rounded-lg border border-red-500/30 bg-gradient-to-r from-red-950/50 to-transparent p-4">
                <div className="flex items-start gap-3">
                  <Sparkles className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-red-100">Why this is on your list</h3>
                    <p className="text-xs leading-relaxed text-zinc-300">
                      Your taste profile lines up closely with this film in our SVD latent-factor model.
                    </p>
                    <ModelBadge strategy={strategy} predictedRating={predicted} />
                  </div>
                </div>
              </div>
            )}

            <p className="text-[15px] leading-relaxed text-zinc-200">
              {movie.overview ||
                `A ${movie.genres?.join(', ').toLowerCase() || 'cinematic'} feature${
                  displayYear(movie) ? ` from ${displayYear(movie)}` : ''
                }, surfaced for you from high collaborative ratings and viewing patterns.`}
            </p>

            {/* Your rating */}
            <div className="rounded-lg bg-white/5 p-4 ring-1 ring-white/10">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-bold">Your rating</h3>
                {effective ? (
                  <span className="flex items-center gap-1 text-xs font-semibold text-emerald-400 animate-fade-in">
                    <Check className="h-3.5 w-3.5" /> Saved
                  </span>
                ) : null}
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <StarRating
                  rating={effective || 0}
                  size="lg"
                  showValue={false}
                  showLabel
                  onRate={(r) => onRate(movie.movieId, r)}
                />
                {effective && onDeleteRating ? (
                  <button
                    onClick={() => onDeleteRating(movie.movieId)}
                    className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold text-zinc-400 transition-colors hover:bg-red-950/60 hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4" /> Remove
                  </button>
                ) : null}
              </div>
              <p className="mt-2 text-xs text-zinc-500">Every rating sharpens your recommendations.</p>
            </div>
          </div>

          {/* Side meta */}
          <aside className="space-y-4 text-sm">
            {movie.genres?.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs text-zinc-500">Genres</p>
                <div className="flex flex-wrap gap-1.5">
                  {movie.genres.map((g) => (
                    <span key={g} className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-medium text-zinc-200">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {movie.tmdbId ? (
              <a
                href={`https://www.themoviedb.org/movie/${Math.round(movie.tmdbId)}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-400 transition-colors hover:text-white"
              >
                View on TMDb <ExternalLink className="h-3.5 w-3.5" />
              </a>
            ) : null}
          </aside>
        </div>
      </div>
    </div>
  );
};
