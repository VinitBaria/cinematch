import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search as SearchIcon, X, Clapperboard } from 'lucide-react';
import { Movie, RecommendationItem } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { MovieCard, MovieCardSkeleton } from '../components/MovieCard';
import { MovieModal } from '../components/MovieModal';

const GENRES = [
  'All', 'Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary',
  'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller',
];

const SORTS = [
  { value: 'popular', label: 'Popular' },
  { value: 'rating', label: 'Top Rated' },
  { value: 'newest', label: 'Newest' },
  { value: 'title', label: 'A–Z' },
];

export const Search: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlQuery = searchParams.get('q') || '';
  const urlGenre = searchParams.get('genre') || 'All';

  const { isAuthenticated } = useAuth();
  const [query, setQuery] = useState(urlQuery);
  const [selectedGenre, setSelectedGenre] = useState<string>(GENRES.includes(urlGenre) ? urlGenre : 'All');
  const [sortBy, setSortBy] = useState<string>('popular');
  const [movies, setMovies] = useState<Movie[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userRatings, setUserRatings] = useState<Record<number, number>>({});
  const [selectedMovie, setSelectedMovie] = useState<Movie | RecommendationItem | null>(null);

  // Keep local state in sync when the URL changes from elsewhere (navbar search, "Explore all" links)
  useEffect(() => {
    setQuery(urlQuery);
    setSelectedGenre(GENRES.includes(urlGenre) ? urlGenre : 'All');
  }, [urlQuery, urlGenre]);

  useEffect(() => {
    if (!isAuthenticated) return;
    api
      .getUserRatings(200)
      .then((ratings) => {
        const map: Record<number, number> = {};
        ratings.forEach((r) => (map[r.movieId] = r.rating));
        setUserRatings(map);
      })
      .catch(() => {});
  }, [isAuthenticated]);

  useEffect(() => {
    let cancelled = false;
    const fetchMovies = async () => {
      setIsLoading(true);
      try {
        if (query.trim()) {
          const results = await api.searchMovies(query.trim(), 40);
          if (!cancelled) setMovies(results);
        } else {
          const res = await api.getMovies({
            genre: selectedGenre === 'All' ? undefined : selectedGenre,
            sort_by: sortBy,
            page_size: 36,
          });
          if (!cancelled) setMovies(res.movies);
        }
      } catch (err) {
        console.error('Failed to search/filter movies:', err);
        if (!cancelled) setMovies([]);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };
    const t = setTimeout(fetchMovies, 250);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [query, selectedGenre, sortBy]);

  const updateParams = (q: string, genre: string) => {
    const p: Record<string, string> = {};
    if (q) p.q = q;
    if (!q && genre !== 'All') p.genre = genre;
    setSearchParams(p, { replace: true });
  };

  const handleRateMovie = async (movieId: number, rating: number) => {
    setUserRatings((prev) => ({ ...prev, [movieId]: rating }));
    try {
      await api.submitRating(movieId, rating);
    } catch (err) {
      console.error('Error submitting rating:', err);
    }
  };

  const handleDeleteRating = async (movieId: number) => {
    setUserRatings((prev) => {
      const c = { ...prev };
      delete c[movieId];
      return c;
    });
    try {
      await api.deleteRating(movieId);
    } catch (err) {
      console.error(err);
    }
  };

  const searching = !!query.trim();

  return (
    <div className="mx-auto min-h-screen max-w-[1800px] px-4 pb-20 pt-24 md:px-12 md:pt-28">
      {/* Header + search */}
      <div className="mb-8 animate-fade-up">
        <h1 className="mb-5 font-display text-5xl tracking-wide text-white md:text-6xl">Browse</h1>

        <div className="group relative max-w-3xl">
          <SearchIcon className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-zinc-500 transition-colors group-focus-within:text-white" />
          <input
            type="text"
            placeholder="Search titles — Inception, Toy Story, Pulp Fiction…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              updateParams(e.target.value, selectedGenre);
            }}
            className="h-14 w-full rounded-lg border border-white/10 bg-white/5 pl-12 pr-12 text-base text-white placeholder-zinc-500 outline-none transition-all focus:border-white/40 focus:bg-white/10 focus:shadow-[0_0_0_4px_rgba(229,9,20,0.15)]"
          />
          {query && (
            <button
              onClick={() => {
                setQuery('');
                updateParams('', selectedGenre);
              }}
              aria-label="Clear search"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1.5 text-zinc-400 transition-colors hover:bg-white/10 hover:text-white animate-scale-in"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Genre pills + sort */}
      <div className="sticky top-16 z-30 -mx-4 mb-8 bg-[#141414]/90 px-4 py-3 backdrop-blur-md md:top-[68px] md:-mx-12 md:px-12">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="no-scrollbar flex items-center gap-2 overflow-x-auto py-1">
            {GENRES.map((g) => {
              const active = selectedGenre === g && !searching;
              return (
                <button
                  key={g}
                  onClick={() => {
                    setSelectedGenre(g);
                    setQuery('');
                    updateParams('', g);
                  }}
                  className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-semibold transition-all duration-300 ${
                    active
                      ? 'scale-105 bg-white text-black shadow-lg'
                      : 'bg-white/10 text-zinc-300 hover:bg-white/20 hover:text-white'
                  }`}
                >
                  {g}
                </button>
              );
            })}
          </div>

          <div
            className={`flex flex-shrink-0 items-center rounded-lg bg-white/5 p-1 transition-opacity ${
              searching ? 'pointer-events-none opacity-40' : ''
            }`}
            role="tablist"
            aria-label="Sort"
          >
            {SORTS.map((s) => (
              <button
                key={s.value}
                role="tab"
                aria-selected={sortBy === s.value}
                onClick={() => setSortBy(s.value)}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-all duration-300 ${
                  sortBy === s.value ? 'bg-[#e50914] text-white shadow' : 'text-zinc-400 hover:text-white'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {!isLoading && (
        <p className="mb-4 text-sm text-zinc-400 animate-fade-in">
          {searching ? (
            <>
              <strong className="text-white">{movies.length}</strong> results for “{query}”
            </>
          ) : (
            <>
              <strong className="text-white">{movies.length}</strong> titles
              {selectedGenre !== 'All' && <> in {selectedGenre}</>}
            </>
          )}
        </p>
      )}

      {/* Grid */}
      {isLoading ? (
        <Grid>
          {Array.from({ length: 18 }).map((_, i) => (
            <MovieCardSkeleton key={i} fluid />
          ))}
        </Grid>
      ) : movies.length > 0 ? (
        <Grid>
          {movies.map((movie, i) => (
            <MovieCard
              key={movie.movieId}
              fluid
              index={i}
              movie={movie}
              onSelect={(m) => setSelectedMovie(m)}
              onRate={handleRateMovie}
              userRating={userRatings[movie.movieId]}
            />
          ))}
        </Grid>
      ) : (
        <div className="flex flex-col items-center rounded-xl border border-dashed border-white/10 py-24 text-center animate-fade-up">
          <Clapperboard className="mb-4 h-12 w-12 text-zinc-700" />
          <p className="text-lg font-semibold text-white">
            {searching ? `Nothing found for “${query}”` : 'No titles here yet'}
          </p>
          <p className="mt-1 text-sm text-zinc-500">Try a different title or genre.</p>
        </div>
      )}

      <MovieModal
        movie={selectedMovie}
        isOpen={!!selectedMovie}
        onClose={() => setSelectedMovie(null)}
        onRate={handleRateMovie}
        onDeleteRating={handleDeleteRating}
        userRating={selectedMovie ? userRatings[selectedMovie.movieId] : undefined}
      />
    </div>
  );
};

const Grid: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7">
    {children}
  </div>
);
