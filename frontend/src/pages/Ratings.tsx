import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Star, Film, Trash2, ArrowRight, Heart } from 'lucide-react';
import { Rating, Movie } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StarRating } from '../components/StarRating';
import { MovieModal } from '../components/MovieModal';
import { Poster } from '../components/Poster';
import { useCountUp } from '../hooks/useCountUp';

type SortKey = 'recent' | 'high' | 'low';

export const Ratings: React.FC = () => {
  const { isAuthenticated, user, refreshUser } = useAuth();

  const [ratings, setRatings] = useState<Rating[]>([]);
  const [movieMap, setMovieMap] = useState<Record<number, Movie>>({});
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<number | null>(null);
  const [sort, setSort] = useState<SortKey>('recent');

  useEffect(() => {
    const fetchRatings = async () => {
      setIsLoading(true);
      try {
        if (isAuthenticated) {
          const userRatings = await api.getUserRatings(200);
          setRatings(userRatings);

          const loaded = await Promise.all(
            userRatings.slice(0, 50).map((r) => api.getMovieById(r.movieId).catch(() => null))
          );
          const map: Record<number, Movie> = {};
          loaded.forEach((m) => {
            if (m) map[m.movieId] = m;
          });
          setMovieMap(map);
        }
      } catch (err) {
        console.error('Failed to load ratings:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchRatings();
  }, [isAuthenticated, user?.userId]);

  const handleUpdateRating = async (movieId: number, newRating: number) => {
    setRatings((prev) => prev.map((r) => (r.movieId === movieId ? { ...r, rating: newRating } : r)));
    try {
      await api.submitRating(movieId, newRating);
      refreshUser();
    } catch (err) {
      console.error('Failed to update rating:', err);
    }
  };

  const handleDeleteRating = async (movieId: number) => {
    setRatings((prev) => prev.filter((r) => r.movieId !== movieId));
    if (selectedMovie && selectedMovie.movieId === movieId) setSelectedMovie(null);
    try {
      await api.deleteRating(movieId);
      refreshUser();
    } catch (err) {
      console.error('Failed to delete rating:', err);
    }
  };

  const totalCount = ratings.length;
  const avg = totalCount > 0 ? ratings.reduce((a, r) => a + r.rating, 0) / totalCount : 0;
  const fiveStars = ratings.filter((r) => r.rating === 5).length;
  const distribution = useMemo(
    () => [5, 4, 3, 2, 1].map((s) => ({ star: s, count: ratings.filter((r) => Math.round(r.rating) === s).length })),
    [ratings]
  );
  const maxBucket = Math.max(1, ...distribution.map((d) => d.count));

  const visible = useMemo(() => {
    let list = filter ? ratings.filter((r) => Math.round(r.rating) === filter) : [...ratings];
    if (sort === 'high') list.sort((a, b) => b.rating - a.rating);
    if (sort === 'low') list.sort((a, b) => a.rating - b.rating);
    return list;
  }, [ratings, filter, sort]);

  const countTotal = useCountUp(totalCount);
  const countAvg = useCountUp(avg, 900, 2);
  const countFive = useCountUp(fiveStars);

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 text-center animate-fade-up">
        <Star className="mb-4 h-14 w-14 text-zinc-700" />
        <h2 className="mb-2 text-2xl font-bold text-white">Sign in to see your ratings</h2>
        <p className="mb-6 max-w-sm text-zinc-400">Track everything you've watched and teach the AI your taste.</p>
        <Link to="/login" className="rounded-md bg-[#e50914] px-8 py-3 text-sm font-bold text-white transition-all hover:bg-[#f6121d] active:scale-95">
          Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-[1800px] px-4 pb-20 pt-24 md:px-12 md:pt-28">
      {/* Header */}
      <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end animate-fade-up">
        <div>
          <h1 className="font-display text-5xl tracking-wide text-white md:text-7xl">My Ratings</h1>
          <p className="mt-2 text-sm text-zinc-400">Every rating helps tune your recommendations.</p>
        </div>
        <Link
          to="/search"
          className="group inline-flex items-center gap-2 self-start rounded-md bg-white/10 px-4 py-2.5 text-sm font-semibold text-white transition-all hover:bg-white/20 md:self-auto"
        >
          Find more to rate
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>

      {/* Stats */}
      <div className="mb-10 grid gap-3 md:grid-cols-[1fr_1fr_1fr_1.6fr]">
        <StatTile label="Films rated" value={countTotal} icon={<Film className="h-5 w-5 text-zinc-400" />} delay={0} />
        <StatTile label="Average score" value={`★ ${countAvg}`} valueClass="text-amber-400" delay={80} />
        <StatTile label="Five-star favorites" value={countFive} valueClass="text-emerald-400" icon={<Heart className="h-5 w-5 text-emerald-500/60" />} delay={160} />

        {/* Distribution */}
        <div className="rounded-xl bg-white/[0.04] p-4 ring-1 ring-white/10 animate-fade-up" style={{ animationDelay: '240ms' }}>
          <p className="mb-2 text-xs text-zinc-400">Rating distribution</p>
          <div className="space-y-1.5">
            {distribution.map((d) => (
              <button
                key={d.star}
                onClick={() => setFilter((f) => (f === d.star ? null : d.star))}
                className="group flex w-full items-center gap-2 text-xs"
                aria-pressed={filter === d.star}
              >
                <span className={`w-4 text-right font-semibold ${filter === d.star ? 'text-amber-400' : 'text-zinc-400'}`}>{d.star}★</span>
                <span className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                  <span
                    className={`block h-full rounded-full transition-all duration-1000 ease-out ${
                      filter === d.star ? 'bg-amber-400' : 'bg-[#e50914] group-hover:bg-red-500'
                    }`}
                    style={{ width: `${(d.count / maxBucket) * 100}%` }}
                  />
                </span>
                <span className="w-5 text-zinc-500 tabular-nums">{d.count}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Toolbar */}
      {totalCount > 0 && (
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-zinc-400">
            {filter ? (
              <>
                Showing <strong className="text-white">{visible.length}</strong> film{visible.length === 1 ? '' : 's'} rated {filter}★{' '}
                <button onClick={() => setFilter(null)} className="ml-1 font-semibold text-white underline-offset-2 hover:underline">
                  Clear
                </button>
              </>
            ) : (
              <>
                <strong className="text-white">{visible.length}</strong> films
              </>
            )}
          </p>
          <div className="flex items-center rounded-lg bg-white/5 p-1" role="tablist" aria-label="Sort ratings">
            {(
              [
                ['recent', 'Recent'],
                ['high', 'Highest'],
                ['low', 'Lowest'],
              ] as [SortKey, string][]
            ).map(([k, label]) => (
              <button
                key={k}
                role="tab"
                aria-selected={sort === k}
                onClick={() => setSort(k)}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-all duration-300 ${
                  sort === k ? 'bg-[#e50914] text-white' : 'text-zinc-400 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* List */}
      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-32 rounded-xl skeleton" />
          ))}
        </div>
      ) : visible.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {visible.map((r, i) => {
            const movie = movieMap[r.movieId];
            const stub: Movie = movie ?? {
              movieId: r.movieId,
              title: r.title || `Movie #${r.movieId}`,
              genres: [],
              posterUrl: r.posterUrl,
            };
            return (
              <div
                key={r.movieId}
                role="button"
                tabIndex={0}
                onClick={() => movie && setSelectedMovie(movie)}
                onKeyDown={(e) => e.key === 'Enter' && movie && setSelectedMovie(movie)}
                style={{ animationDelay: `${Math.min(i, 16) * 40}ms` }}
                className="group flex cursor-pointer gap-4 rounded-xl bg-white/[0.04] p-3 ring-1 ring-white/10 transition-all duration-300 hover:-translate-y-1 hover:bg-white/[0.08] hover:shadow-xl hover:shadow-black/50 hover:ring-white/25 animate-fade-up"
              >
                <Poster movie={stub} className="h-28 w-[75px] flex-none rounded-md" showFallbackTitle={false} />
                <div className="flex min-w-0 flex-1 flex-col justify-between py-0.5">
                  <div>
                    <h3 className="line-clamp-2 text-sm font-bold leading-tight text-white transition-colors group-hover:text-[#ff4b55]">
                      {stub.cleanTitle || stub.title}
                    </h3>
                    {movie?.year ? <p className="mt-0.5 text-xs text-zinc-500">{Math.round(movie.year)}</p> : null}
                  </div>
                  <div className="flex items-center justify-between" onClick={(e) => e.stopPropagation()}>
                    <StarRating rating={r.rating} size="sm" showValue={false} onRate={(s) => handleUpdateRating(r.movieId, s)} />
                    <button
                      onClick={() => handleDeleteRating(r.movieId)}
                      aria-label={`Remove rating for ${stub.title}`}
                      className="rounded p-1.5 text-zinc-600 opacity-0 transition-all hover:bg-red-950/60 hover:text-red-400 focus-visible:opacity-100 group-hover:opacity-100"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center rounded-xl border border-dashed border-white/10 py-24 text-center animate-fade-up">
          <Star className="mb-4 h-12 w-12 text-zinc-700" />
          <p className="mb-1 text-lg font-semibold text-white">{filter ? `No ${filter}★ ratings yet` : "You haven't rated anything yet"}</p>
          <p className="mb-5 text-sm text-zinc-500">Rate a few films to unlock tailored picks.</p>
          <Link to="/onboarding" className="rounded-md bg-[#e50914] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#f6121d]">
            Start rating
          </Link>
        </div>
      )}

      <MovieModal
        movie={selectedMovie}
        isOpen={!!selectedMovie}
        onClose={() => setSelectedMovie(null)}
        onRate={handleUpdateRating}
        onDeleteRating={handleDeleteRating}
        userRating={selectedMovie ? ratings.find((r) => r.movieId === selectedMovie.movieId)?.rating : undefined}
      />
    </div>
  );
};

const StatTile: React.FC<{
  label: string;
  value: string | number;
  valueClass?: string;
  icon?: React.ReactNode;
  delay?: number;
}> = ({ label, value, valueClass = 'text-white', icon, delay = 0 }) => (
  <div
    className="flex items-center justify-between rounded-xl bg-white/[0.04] p-5 ring-1 ring-white/10 animate-fade-up"
    style={{ animationDelay: `${delay}ms` }}
  >
    <div>
      <p className="mb-1 text-xs text-zinc-400">{label}</p>
      <p className={`text-3xl font-black tabular-nums ${valueClass}`}>{value}</p>
    </div>
    {icon}
  </div>
);
