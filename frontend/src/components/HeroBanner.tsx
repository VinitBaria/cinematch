import React, { useEffect, useState } from 'react';
import { Play, Info, Sparkles, Star } from 'lucide-react';
import { StarRating } from './StarRating';
import { Poster } from './Poster';
import {
  AnyMovie,
  displayTitle,
  displayYear,
  isRecommendation,
  matchPercent,
} from '../utils/movie';

interface HeroBannerProps {
  /** Up to ~5 featured titles; the hero auto-rotates between them. */
  movies: AnyMovie[];
  isLoading?: boolean;
  onMoreInfo: (movie: AnyMovie) => void;
  onRate?: (movieId: number, rating: number) => void;
  userRatings?: Record<number, number>;
}

const SLIDE_MS = 9000;

export const HeroBanner: React.FC<HeroBannerProps> = ({
  movies,
  isLoading = false,
  onMoreInfo,
  onRate,
  userRatings = {},
}) => {
  const slides = movies.slice(0, 5);
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(false);

  // Pause when the tab is in the background
  useEffect(() => {
    const onVis = () => setHidden(document.hidden);
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  // Auto-advance
  useEffect(() => {
    if (slides.length < 2 || paused || hidden) return;
    const id = window.setTimeout(() => setActive((i) => (i + 1) % slides.length), SLIDE_MS);
    return () => window.clearTimeout(id);
  }, [active, slides.length, paused, hidden]);

  useEffect(() => {
    if (active >= slides.length) setActive(0);
  }, [slides.length, active]);

  if (isLoading || slides.length === 0) {
    return (
      <div className="relative h-[70vh] min-h-[460px] w-full overflow-hidden bg-[#0e0e0e] md:h-[88vh]">
        <div className="absolute inset-0 skeleton opacity-40" />
        <div className="absolute bottom-24 left-4 space-y-4 md:left-12">
          <div className="h-5 w-40 rounded skeleton" />
          <div className="h-14 w-[min(520px,80vw)] rounded skeleton" />
          <div className="h-4 w-[min(420px,70vw)] rounded skeleton" />
          <div className="flex gap-3 pt-2">
            <div className="h-11 w-32 rounded skeleton" />
            <div className="h-11 w-36 rounded skeleton" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <section
      className="relative h-[72vh] min-h-[480px] w-full select-none overflow-hidden bg-black md:h-[90vh]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-roledescription="carousel"
      aria-label="Featured titles"
    >
      {/* Layers: one per slide, cross-faded */}
      {slides.map((movie, i) => {
        const isActive = i === active;
        return (
          <div
            key={movie.movieId}
            aria-hidden={!isActive}
            className={`absolute inset-0 transition-opacity duration-[1200ms] ease-in-out ${
              isActive ? 'opacity-100' : 'pointer-events-none opacity-0'
            }`}
          >
            {/* Blurred, slowly-zooming poster as cinematic backdrop */}
            {movie.posterUrl ? (
              <img
                src={movie.posterUrl}
                alt=""
                referrerPolicy="no-referrer"
                className={`absolute inset-0 h-full w-full scale-125 object-cover object-top blur-2xl saturate-150 brightness-[0.55] ${
                  isActive ? 'animate-kenburns' : ''
                }`}
              />
            ) : (
              <div className="absolute inset-0 bg-gradient-to-br from-red-950 via-zinc-900 to-black" />
            )}

            {/* Floating sharp poster (desktop) */}
            <div className="absolute bottom-0 right-[6%] top-0 hidden items-center lg:flex xl:right-[10%]">
              <div
                className={`${isActive ? 'animate-float' : ''} relative w-[300px] xl:w-[340px]`}
                style={{ perspective: 1000 }}
              >
                <div className="absolute -inset-6 rounded-3xl bg-[#e50914]/20 blur-3xl" />
                <Poster
                  movie={movie}
                  eager={i === 0}
                  className="relative aspect-[2/3] rounded-xl shadow-2xl shadow-black ring-1 ring-white/15"
                />
              </div>
            </div>
          </div>
        );
      })}

      {/* Gradients blend into the page */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/55 to-transparent" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-[#141414] via-[#141414]/60 to-transparent" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-black/70 to-transparent" />

      {/* Copy — keyed on slide so entrance animations replay */}
      {(() => {
        const movie = slides[active];
        const rec = isRecommendation(movie);
        const match = matchPercent(movie);
        return (
          <div
            key={movie.movieId}
            className="relative z-20 mx-auto flex h-full max-w-[1800px] flex-col justify-end px-4 pb-28 md:px-12 md:pb-36"
          >
            <div className="max-w-2xl">
              <div className="mb-3 flex flex-wrap items-center gap-2.5 animate-fade-up">
                <span className="inline-flex items-center gap-1.5 text-xs font-black uppercase tracking-[0.2em] text-[#e50914]">
                  <Sparkles className="h-3.5 w-3.5" />
                  {rec ? 'Picked for you' : 'Featured'}
                </span>
              </div>

              <h1
                className="font-display text-5xl leading-[0.95] tracking-wide text-white drop-shadow-[0_4px_24px_rgba(0,0,0,0.6)] sm:text-7xl md:text-8xl animate-fade-up"
                style={{ animationDelay: '80ms' }}
              >
                {displayTitle(movie)}
              </h1>

              <div
                className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 text-sm font-semibold animate-fade-up"
                style={{ animationDelay: '160ms' }}
              >
                {match && <span className="text-base font-bold text-emerald-400">{match}% Match</span>}
                {displayYear(movie) && <span className="text-zinc-300">{displayYear(movie)}</span>}
                {movie.avgRating ? (
                  <span className="flex items-center gap-1 text-amber-400">
                    <Star className="h-4 w-4 fill-amber-400" />
                    {movie.avgRating.toFixed(1)}
                  </span>
                ) : null}
                {movie.genres?.slice(0, 3).map((g) => (
                  <span key={g} className="rounded border border-white/30 px-1.5 py-px text-[11px] text-zinc-200">
                    {g}
                  </span>
                ))}
              </div>

              <p
                className="mt-4 line-clamp-3 max-w-xl text-sm leading-relaxed text-zinc-200 drop-shadow md:text-lg animate-fade-up"
                style={{ animationDelay: '240ms' }}
              >
                {movie.overview ||
                  'Matched to your taste using collaborative filtering — rate a few more films to sharpen your picks.'}
              </p>

              <div
                className="mt-6 flex flex-wrap items-center gap-3 animate-fade-up"
                style={{ animationDelay: '320ms' }}
              >
                <button
                  onClick={() => onMoreInfo(movie)}
                  className="group/btn flex items-center gap-2.5 rounded-md bg-white px-6 py-2.5 text-base font-bold text-black shadow-xl transition-all duration-200 hover:bg-white/80 active:scale-95 md:px-8 md:py-3"
                >
                  <Play className="h-6 w-6 fill-black transition-transform group-hover/btn:scale-110" />
                  Play
                </button>
                <button
                  onClick={() => onMoreInfo(movie)}
                  className="flex items-center gap-2.5 rounded-md bg-zinc-500/50 px-6 py-2.5 text-base font-bold text-white shadow-xl backdrop-blur-md transition-all duration-200 hover:bg-zinc-500/35 active:scale-95 md:px-8 md:py-3"
                >
                  <Info className="h-6 w-6" />
                  More Info
                </button>

                {onRate && (
                  <div className="hidden items-center gap-3 rounded-md border border-white/10 bg-black/40 px-4 py-2 backdrop-blur-md md:flex">
                    <span className="text-xs font-semibold text-zinc-300">Rate</span>
                    <StarRating
                      rating={userRatings[movie.movieId] || 0}
                      size="md"
                      showValue={false}
                      onRate={(r) => onRate(movie.movieId, r)}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {/* Slide indicators with progress */}
      {slides.length > 1 && (
        <div className="absolute bottom-24 right-4 z-30 flex items-center gap-2 md:bottom-32 md:right-12">
          {slides.map((m, i) => (
            <button
              key={m.movieId}
              onClick={() => setActive(i)}
              aria-label={`Show ${displayTitle(m)}`}
              aria-current={i === active}
              className="group/dot relative h-1.5 w-8 overflow-hidden rounded-full bg-white/25 transition-all hover:bg-white/40 md:w-12"
            >
              {i === active && (
                <span
                  key={`${active}-${paused}`}
                  className="absolute inset-0 origin-left rounded-full bg-white"
                  style={
                    paused
                      ? { transform: 'scaleX(1)', opacity: 0.8 }
                      : { animation: `progress ${SLIDE_MS}ms linear both` }
                  }
                />
              )}
              {i < active && <span className="absolute inset-0 rounded-full bg-white/70" />}
            </button>
          ))}
        </div>
      )}
    </section>
  );
};
