import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Check } from 'lucide-react';
import { Movie } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StarRating } from '../components/StarRating';
import { Poster } from '../components/Poster';
import { MovieCardSkeleton } from '../components/MovieCard';

const REQUIRED_RATINGS = 5;

export const Onboarding: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, refreshUser } = useAuth();

  const [movies, setMovies] = useState<Movie[]>([]);
  const [ratedCount, setRatedCount] = useState<number>(0);
  const [userRatings, setUserRatings] = useState<Record<number, number>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadPicks = async () => {
      setIsLoading(true);
      try {
        const picks = await api.getOnboardingPicks(30);
        setMovies(picks);

        if (isAuthenticated) {
          const existing = await api.getUserRatings(200);
          const map: Record<number, number> = {};
          existing.forEach((r) => (map[r.movieId] = r.rating));
          setUserRatings(map);
          setRatedCount(existing.length);
        }
      } catch (err) {
        console.error('Failed to load onboarding picks:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadPicks();
  }, [isAuthenticated]);

  const handleRateMovie = async (movieId: number, rating: number) => {
    const isNew = !userRatings[movieId];
    setUserRatings((prev) => ({ ...prev, [movieId]: rating }));
    if (isNew) setRatedCount((c) => c + 1);
    try {
      await api.submitRating(movieId, rating);
      refreshUser();
    } catch (err) {
      console.error('Error submitting rating:', err);
    }
  };

  const pct = Math.min(100, Math.round((ratedCount / REQUIRED_RATINGS) * 100));
  const isReady = ratedCount >= REQUIRED_RATINGS;
  const remaining = Math.max(0, REQUIRED_RATINGS - ratedCount);

  return (
    <div className="mx-auto min-h-screen max-w-[1800px] px-4 pb-40 pt-24 md:px-12 md:pt-28">
      {/* Intro */}
      <div className="mx-auto mb-12 max-w-3xl text-center">
        <span className="mb-4 inline-flex items-center gap-2 rounded-full bg-[#e50914]/15 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-red-300 ring-1 ring-[#e50914]/40 animate-fade-down">
          <Sparkles className="h-3.5 w-3.5" /> Let's learn your taste
        </span>
        <h1 className="font-display text-6xl leading-none tracking-wide text-white md:text-8xl animate-fade-up">
          What do you <span className="text-gradient-red">love</span> watching?
        </h1>
        <p className="mt-4 text-base text-zinc-400 animate-fade-up" style={{ animationDelay: '120ms' }}>
          Rate at least <strong className="text-white">{REQUIRED_RATINGS} films</strong> you've seen. The more you rate, the sharper your picks.
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-5 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {isLoading
          ? Array.from({ length: 18 }).map((_, i) => <MovieCardSkeleton key={i} fluid />)
          : movies.map((movie, i) => {
              const current = userRatings[movie.movieId];
              const rated = !!current;
              return (
                <div
                  key={movie.movieId}
                  style={{ animationDelay: `${Math.min(i, 18) * 35}ms` }}
                  className={`group relative overflow-hidden rounded-lg bg-[#1c1c1c] transition-all duration-300 animate-fade-up ${
                    rated
                      ? 'ring-2 ring-emerald-400 shadow-lg shadow-emerald-950/40'
                      : 'ring-1 ring-white/10 hover:-translate-y-1 hover:ring-white/30'
                  }`}
                >
                  <div className="relative">
                    <Poster
                      movie={movie}
                      className={`aspect-[2/3] w-full transition-all duration-500 ${rated ? 'brightness-[0.55]' : ''}`}
                      imgClassName="group-hover:scale-105"
                    />
                    {rated && (
                      <span className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-emerald-400 text-black shadow-lg animate-pop">
                        <Check className="h-4 w-4" strokeWidth={3} />
                      </span>
                    )}
                    <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black via-black/70 to-transparent px-3 pb-2 pt-12">
                      <p className="line-clamp-1 text-xs font-bold text-white">{movie.cleanTitle || movie.title}</p>
                      {movie.year ? <p className="text-[11px] text-zinc-400">{Math.round(movie.year)}</p> : null}
                    </div>
                  </div>
                  <div className="flex justify-center bg-[#181818] py-2.5">
                    <StarRating rating={current || 0} size="md" showValue={false} onRate={(r) => handleRateMovie(movie.movieId, r)} />
                  </div>
                </div>
              );
            })}
      </div>

      {/* Sticky progress dock */}
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-40 flex justify-center px-4 pb-5">
        <div className="pointer-events-auto flex w-full max-w-3xl items-center gap-4 rounded-2xl bg-[#181818]/90 p-3 pl-5 shadow-2xl shadow-black ring-1 ring-white/10 backdrop-blur-xl animate-slide-up sm:gap-6">
          {/* Ring */}
          <div className="relative h-12 w-12 flex-none">
            <svg viewBox="0 0 36 36" className="h-12 w-12 -rotate-90">
              <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3" />
              <circle
                cx="18"
                cy="18"
                r="15.5"
                fill="none"
                stroke={isReady ? '#34d399' : '#e50914'}
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={`${(pct / 100) * 97.4} 97.4`}
                className="transition-all duration-700 ease-out"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-sm font-black tabular-nums text-white">
              {Math.min(ratedCount, REQUIRED_RATINGS)}
            </span>
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold text-white">
              {isReady ? "You're all set!" : `Rate ${remaining} more to unlock your picks`}
            </p>
            <p className="truncate text-xs text-zinc-400">
              {ratedCount} rated{ratedCount > REQUIRED_RATINGS ? ' — keep going for better results' : ''}
            </p>
          </div>

          <button
            onClick={() => navigate('/recommendations')}
            disabled={!isReady}
            className={`flex flex-none items-center gap-2 rounded-xl px-5 py-3 text-sm font-bold transition-all duration-300 ${
              isReady
                ? 'animate-glow bg-[#e50914] text-white hover:bg-[#f6121d] active:scale-95'
                : 'bg-white/10 text-zinc-500'
            }`}
          >
            <span className="hidden sm:inline">See my picks</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
