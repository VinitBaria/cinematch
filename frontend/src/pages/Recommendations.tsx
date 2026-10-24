import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, ChevronDown, Play, Star, Cpu } from 'lucide-react';
import { RecommendationItem, Movie, ModelInfo } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { MovieCard, MovieCardSkeleton } from '../components/MovieCard';
import { MovieModal } from '../components/MovieModal';
import { Poster } from '../components/Poster';
import { ModelBadge } from '../components/ModelBadge';
import { Reveal } from '../components/Reveal';
import { displayTitle, displayYear, matchPercent } from '../utils/movie';

export const Recommendations: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [strategy, setStrategy] = useState<string>('svd_matrix_factorization');
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [userRatings, setUserRatings] = useState<Record<number, number>>({});
  const [selectedMovie, setSelectedMovie] = useState<Movie | RecommendationItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showModel, setShowModel] = useState(false);

  useEffect(() => {
    const loadRecs = async () => {
      setIsLoading(true);
      try {
        const recsRes = await api.getRecommendations(24);
        setRecommendations(recsRes.recommendations);
        setStrategy(recsRes.strategy);

        api.getModelInfo().then(setModelInfo).catch(() => {});

        if (isAuthenticated) {
          const ratingsRes = await api.getUserRatings(200);
          const map: Record<number, number> = {};
          ratingsRes.forEach((r) => (map[r.movieId] = r.rating));
          setUserRatings(map);
        }
      } catch (err) {
        console.error('Failed to load recommendations:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadRecs();
  }, [isAuthenticated, user?.userId]);

  const handleRateMovie = async (movieId: number, rating: number) => {
    setUserRatings((prev) => ({ ...prev, [movieId]: rating }));
    try {
      await api.submitRating(movieId, rating);
      const recsRes = await api.getRecommendations(24);
      setRecommendations(recsRes.recommendations);
      setStrategy(recsRes.strategy);
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

  const isColdStart = strategy.includes('popularity') || (user && user.ratingCount === 0);
  const [spotlight, ...rest] = recommendations;

  return (
    <div className="mx-auto min-h-screen max-w-[1800px] px-4 pb-20 pt-24 md:px-12 md:pt-28">
      {/* Header */}
      <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end animate-fade-up">
        <div>
          <p className="mb-2 inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.25em] text-[#e50914]">
            <Sparkles className="h-4 w-4 animate-pulse" /> Made for {user?.name?.split(' ')[0] || 'you'}
          </p>
          <h1 className="font-display text-5xl tracking-wide text-white md:text-7xl">AI Picks</h1>
          <p className="mt-2 max-w-xl text-sm text-zinc-400">
            Ranked by how closely each film matches your taste profile — updated every time you rate.
          </p>
        </div>

        {isColdStart && (
          <Link
            to="/onboarding"
            className="group inline-flex items-center gap-2 self-start rounded-md bg-[#e50914] px-5 py-3 text-sm font-bold text-white shadow-lg shadow-red-950/50 transition-all hover:bg-[#f6121d] active:scale-95 md:self-auto"
          >
            Rate movies to improve
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        )}
      </div>

      {/* Spotlight: #1 match */}
      {isLoading ? (
        <div className="mb-10 h-72 rounded-2xl skeleton" />
      ) : spotlight ? (
        <div
          className="group/spot relative mb-10 cursor-pointer overflow-hidden rounded-2xl bg-[#1a1a1a] ring-1 ring-white/10 transition-all duration-500 hover:ring-white/30 animate-fade-up"
          onClick={() => setSelectedMovie(spotlight)}
        >
          {spotlight.posterUrl && (
            <img
              src={spotlight.posterUrl}
              alt=""
              referrerPolicy="no-referrer"
              className="absolute inset-0 h-full w-full scale-125 object-cover blur-3xl brightness-[0.35] saturate-150 transition-transform duration-[1500ms] group-hover/spot:scale-150"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/20 to-transparent" />

          <div className="relative flex flex-col items-center gap-6 p-6 sm:flex-row sm:items-center sm:gap-10 sm:p-10">
            <Poster
              movie={spotlight}
              eager
              className="aspect-[2/3] w-40 flex-none rounded-lg shadow-2xl shadow-black ring-1 ring-white/20 transition-transform duration-500 group-hover/spot:scale-105 sm:w-52"
            />
            <div className="text-center sm:text-left">
              <span className="mb-3 inline-block rounded bg-[#e50914] px-2 py-1 text-[11px] font-black uppercase tracking-widest text-white">
                #1 Match for you
              </span>
              <h2 className="font-display text-4xl leading-none tracking-wide text-white sm:text-6xl">
                {displayTitle(spotlight)}
              </h2>
              <div className="mt-3 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-sm font-semibold sm:justify-start">
                <span className="text-lg font-bold text-emerald-400">{matchPercent(spotlight)}% Match</span>
                {displayYear(spotlight) && <span className="text-zinc-300">{displayYear(spotlight)}</span>}
                {spotlight.avgRating ? (
                  <span className="flex items-center gap-1 text-amber-400">
                    <Star className="h-4 w-4 fill-amber-400" />
                    {spotlight.avgRating.toFixed(1)}
                  </span>
                ) : null}
              </div>
              {spotlight.overview && (
                <p className="mt-3 line-clamp-3 max-w-2xl text-sm leading-relaxed text-zinc-300">{spotlight.overview}</p>
              )}
              <div className="mt-5 flex items-center justify-center gap-3 sm:justify-start">
                <span className="inline-flex items-center gap-2 rounded-md bg-white px-6 py-2.5 text-sm font-bold text-black transition-colors group-hover/spot:bg-white/85">
                  <Play className="h-4 w-4 fill-black" /> View details
                </span>
                <ModelBadge strategy={spotlight.recommendationStrategy} predictedRating={spotlight.predictedRating} />
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Collapsible "how it works" */}
      <div className="mb-10 overflow-hidden rounded-xl bg-white/[0.04] ring-1 ring-white/10">
        <button
          onClick={() => setShowModel((s) => !s)}
          aria-expanded={showModel}
          className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-white/5"
        >
          <span className="flex items-center gap-3 text-sm font-semibold text-white">
            <Cpu className="h-4 w-4 text-[#e50914]" />
            How these picks are made
            <span className="hidden rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400 sm:inline">
              {strategy.replace(/_/g, ' ')}
            </span>
          </span>
          <ChevronDown className={`h-5 w-5 text-zinc-400 transition-transform duration-300 ${showModel ? 'rotate-180' : ''}`} />
        </button>
        <div className={`grid transition-all duration-500 ease-out ${showModel ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
          <div className="min-h-0 overflow-hidden">
            <div className="grid grid-cols-2 gap-3 border-t border-white/10 p-5 text-xs sm:grid-cols-4">
              <Stat label="Algorithm" value="SVD Collaborative" />
              <Stat label="Latent factors" value={`${modelInfo?.parameters?.n_factors ?? 100}`} />
              <Stat label="Validation RMSE" value="0.867" accent />
              <Stat
                label="Training ratings"
                value={(modelInfo?.trainsetStats?.n_ratings ?? 70000).toLocaleString() + '+'}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <Grid>
          {Array.from({ length: 12 }).map((_, i) => (
            <MovieCardSkeleton key={i} fluid />
          ))}
        </Grid>
      ) : rest.length > 0 ? (
        <Reveal>
          <h2 className="mb-4 text-xl font-bold text-white md:text-2xl">More you'll love</h2>
          <Grid>
            {rest.map((movie, i) => (
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
        </Reveal>
      ) : !spotlight ? (
        <div className="flex flex-col items-center rounded-xl border border-dashed border-white/10 py-24 text-center">
          <Sparkles className="mb-4 h-12 w-12 text-zinc-700" />
          <p className="mb-4 text-lg font-semibold text-white">No recommendations yet</p>
          <Link to="/onboarding" className="rounded-md bg-[#e50914] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#f6121d]">
            Start rating movies
          </Link>
        </div>
      ) : null}

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

const Stat: React.FC<{ label: string; value: string; accent?: boolean }> = ({ label, value, accent }) => (
  <div className="rounded-lg bg-black/30 p-3 ring-1 ring-white/5">
    <p className="mb-1 text-zinc-500">{label}</p>
    <p className={`text-sm font-bold ${accent ? 'text-emerald-400' : 'text-white'}`}>{value}</p>
  </div>
);

const Grid: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7">
    {children}
  </div>
);
