import React, { useEffect, useState } from 'react';
import { Film } from 'lucide-react';
import { AnyMovie, displayTitle, displayYear, getMoviePoster, posterGradient } from '../utils/movie';

interface PosterProps {
  movie: AnyMovie;
  className?: string;
  imgClassName?: string;
  eager?: boolean;
  /** Show the title on the placeholder when artwork is missing. */
  showFallbackTitle?: boolean;
}

/** Poster with a blur-up fade-in and a guaranteed real cinematic poster fallback when image fails. */
export const Poster: React.FC<PosterProps> = ({
  movie,
  className = '',
  imgClassName = '',
  eager = false,
  showFallbackTitle = true,
}) => {
  const fallbackUrl = getMoviePoster(movie);
  const initialUrl = (movie.posterUrl && movie.posterUrl.trim()) ? movie.posterUrl : fallbackUrl;
  
  const [imgSrc, setImgSrc] = useState(initialUrl);
  const [loaded, setLoaded] = useState(false);
  const [hasFailedOnce, setHasFailedOnce] = useState(false);
  const [totalFail, setTotalFail] = useState(false);
  const title = displayTitle(movie);

  useEffect(() => {
    const nextUrl = (movie.posterUrl && movie.posterUrl.trim()) ? movie.posterUrl : fallbackUrl;
    setImgSrc(nextUrl);
    setLoaded(false);
    setHasFailedOnce(false);
    setTotalFail(false);
  }, [movie.movieId, movie.posterUrl]);

  const handleImageError = () => {
    if (!hasFailedOnce && imgSrc !== fallbackUrl) {
      setHasFailedOnce(true);
      setImgSrc(fallbackUrl);
    } else {
      setTotalFail(true);
    }
  };

  return (
    <div className={`relative overflow-hidden bg-[#1c1c1c] ${className}`}>
      {!totalFail ? (
        <>
          {!loaded && <div className="absolute inset-0 skeleton" />}
          <img
            src={imgSrc}
            alt={title}
            loading={eager ? 'eager' : 'lazy'}
            decoding="async"
            referrerPolicy="no-referrer"
            onLoad={() => setLoaded(true)}
            onError={handleImageError}
            className={`h-full w-full object-cover transition-all duration-700 ${
              loaded ? 'opacity-100 blur-0 scale-100' : 'opacity-0 blur-md scale-105'
            } ${imgClassName}`}
          />
          {hasFailedOnce && showFallbackTitle && (
            <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black via-black/80 to-transparent px-2.5 pb-2 pt-6">
              <p className="line-clamp-1 text-xs font-bold text-white drop-shadow">{title}</p>
              <span className="text-[10px] font-semibold text-zinc-400">{movie.genres?.[0] || 'Movie'}</span>
            </div>
          )}
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
