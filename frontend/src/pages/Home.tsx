import React, { useState, useEffect } from 'react';
import { Sparkles, Flame, Trophy, Swords, Rocket, Smile } from 'lucide-react';
import { Movie, RecommendationItem } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { HeroBanner } from '../components/HeroBanner';
import { MovieCarousel } from '../components/MovieCarousel';
import { MovieModal } from '../components/MovieModal';

export const Home: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [trending, setTrending] = useState<Movie[]>([]);
  const [topRated, setTopRated] = useState<Movie[]>([]);
  const [actionMovies, setActionMovies] = useState<Movie[]>([]);
  const [sciFiMovies, setSciFiMovies] = useState<Movie[]>([]);
  const [comedyMovies, setComedyMovies] = useState<Movie[]>([]);

  const [userRatings, setUserRatings] = useState<Record<number, number>>({});
  const [selectedMovie, setSelectedMovie] = useState<Movie | RecommendationItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load all movie feeds
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [trendingRes, topRatedRes, actionRes, sciFiRes, comedyRes] = await Promise.all([
          api.getTrending(15).catch(() => []),
          api.getTopRated(15).catch(() => []),
          api.getMovies({ genre: 'Action', page_size: 15 }).then((r) => r.movies).catch(() => []),
          api.getMovies({ genre: 'Sci-Fi', page_size: 15 }).then((r) => r.movies).catch(() => []),
          api.getMovies({ genre: 'Comedy', page_size: 15 }).then((r) => r.movies).catch(() => []),
        ]);

        setTrending(trendingRes);
        setTopRated(topRatedRes);
        setActionMovies(actionRes);
        setSciFiMovies(sciFiRes);
        setComedyMovies(comedyRes);

        if (isAuthenticated) {
          try {
            const recsRes = await api.getRecommendations(15);
            setRecommendations(recsRes.recommendations);
          } catch (e) {
            console.warn('Could not fetch recommendations, fallback to trending', e);
          }

          try {
            const ratingsRes = await api.getUserRatings(200);
            const map: Record<number, number> = {};
            ratingsRes.forEach((r) => {
              map[r.movieId] = r.rating;
            });
            setUserRatings(map);
          } catch (e) {
            console.warn('Could not fetch user ratings', e);
          }
        } else {
          setRecommendations([]);
          setUserRatings({});
        }
      } catch (err) {
        console.error('Error fetching home data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, user?.userId]);

  const handleRateMovie = async (movieId: number, rating: number) => {
    setUserRatings((prev) => ({ ...prev, [movieId]: rating }));
    try {
      await api.submitRating(movieId, rating);
      if (isAuthenticated) {
        api
          .getRecommendations(15)
          .then((res) => setRecommendations(res.recommendations))
          .catch(() => {});
      }
    } catch (err) {
      console.error('Failed to submit rating:', err);
    }
  };

  const handleDeleteRating = async (movieId: number) => {
    setUserRatings((prev) => {
      const copy = { ...prev };
      delete copy[movieId];
      return copy;
    });
    try {
      await api.deleteRating(movieId);
    } catch (err) {
      console.error('Failed to delete rating:', err);
    }
  };

  // Hero rotates through top recommendations, falling back to trending titles
  const heroMovies = recommendations.length > 0 ? recommendations : trending;
  const open = (m: Movie | RecommendationItem) => setSelectedMovie(m);

  const rowProps = {
    onSelectMovie: open,
    onRateMovie: handleRateMovie,
    userRatings,
    isLoading,
  };

  return (
    <div className="min-h-screen bg-[#141414] pb-10">
      <HeroBanner
        movies={heroMovies}
        isLoading={isLoading}
        onMoreInfo={open}
        onRate={handleRateMovie}
        userRatings={userRatings}
      />

      {/* Rows overlap the hero's bottom fade like Netflix */}
      <div className="relative z-30 -mt-24 space-y-2 md:-mt-40">
        {recommendations.length > 0 && (
          <MovieCarousel
            title="Top Picks for You"
            subtitle="Generated live from your ratings"
            icon={<Sparkles className="h-5 w-5 animate-glow rounded-full text-[#e50914]" />}
            movies={recommendations}
            href="/recommendations"
            {...rowProps}
          />
        )}

        <MovieCarousel
          title="Top 10 Trending Now"
          icon={<Flame className="h-5 w-5 text-orange-500" />}
          movies={trending}
          ranked
          {...rowProps}
        />

        <MovieCarousel
          title="Top Rated Masterpieces"
          subtitle="Highest rated by the community"
          icon={<Trophy className="h-5 w-5 text-amber-400" />}
          movies={topRated}
          {...rowProps}
        />

        <MovieCarousel
          title="Adrenaline & Action"
          icon={<Swords className="h-5 w-5 text-red-500" />}
          movies={actionMovies}
          href="/search?genre=Action"
          {...rowProps}
        />

        <MovieCarousel
          title="Sci-Fi & Cyberpunk"
          icon={<Rocket className="h-5 w-5 text-purple-400" />}
          movies={sciFiMovies}
          href="/search?genre=Sci-Fi"
          {...rowProps}
        />

        <MovieCarousel
          title="Feel-Good Comedy"
          icon={<Smile className="h-5 w-5 text-yellow-400" />}
          movies={comedyMovies}
          href="/search?genre=Comedy"
          {...rowProps}
        />
      </div>

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
