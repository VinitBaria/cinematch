import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { MovieCard, MovieCardSkeleton } from './MovieCard';
import { Reveal } from './Reveal';
import { AnyMovie } from '../utils/movie';

interface MovieCarouselProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  movies: AnyMovie[];
  onSelectMovie: (movie: AnyMovie) => void;
  onRateMovie?: (movieId: number, rating: number) => void;
  userRatings?: Record<number, number>;
  isLoading?: boolean;
  /** Netflix-style outlined "Top 10" numerals beside each card. */
  ranked?: boolean;
  /** Optional "Explore all" link target. */
  href?: string;
}

export const MovieCarousel: React.FC<MovieCarouselProps> = ({
  title,
  subtitle,
  icon,
  movies,
  onSelectMovie,
  onRateMovie,
  userRatings = {},
  isLoading = false,
  ranked = false,
  href,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canLeft, setCanLeft] = useState(false);
  const [canRight, setCanRight] = useState(false);
  const [page, setPage] = useState(0);
  const [pages, setPages] = useState(1);

  const measure = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    setCanLeft(el.scrollLeft > 8);
    setCanRight(el.scrollLeft < max - 8);
    const total = Math.max(1, Math.ceil(el.scrollWidth / el.clientWidth - 0.05));
    setPages(total);
    setPage(Math.min(total - 1, Math.round(el.scrollLeft / el.clientWidth)));
  }, []);

  useEffect(() => {
    measure();
    const el = scrollRef.current;
    if (!el) return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [measure, movies.length, isLoading]);

  const scroll = (dir: 'left' | 'right') => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollBy({ left: (dir === 'left' ? -1 : 1) * el.clientWidth * 0.85, behavior: 'smooth' });
  };

  if (!isLoading && movies.length === 0) return null;

  return (
    <Reveal>
      <section className="group/row relative my-2 md:my-4" aria-label={title}>
        {/* Row header */}
        <div className="mb-1 flex items-end justify-between px-4 md:px-12">
          <div className="flex items-center gap-2.5">
            {icon}
            <div>
              <h2 className="text-lg font-bold tracking-tight text-white md:text-2xl">
                {href ? (
                  <Link to={href} className="group/title inline-flex items-center gap-2">
                    {title}
                    <span className="flex items-center text-xs font-bold text-cyan-400 opacity-0 transition-all duration-300 -translate-x-2 group-hover/row:translate-x-0 group-hover/row:opacity-100">
                      Explore all <ChevronRight className="h-4 w-4" />
                    </span>
                  </Link>
                ) : (
                  title
                )}
              </h2>
              {subtitle && <p className="mt-0.5 text-xs text-zinc-400">{subtitle}</p>}
            </div>
          </div>

          {/* Page indicator */}
          {pages > 1 && !isLoading && (
            <div className="hidden items-center gap-1 pb-1 opacity-0 transition-opacity group-hover/row:opacity-100 sm:flex" aria-hidden>
              {Array.from({ length: pages }).map((_, i) => (
                <span
                  key={i}
                  className={`h-0.5 w-4 rounded-full transition-colors duration-300 ${
                    i === page ? 'bg-zinc-200' : 'bg-zinc-700'
                  }`}
                />
              ))}
            </div>
          )}
        </div>

        <div className="relative">
          {/* Left arrow */}
          <button
            onClick={() => scroll('left')}
            aria-label={`Scroll ${title} left`}
            tabIndex={canLeft ? 0 : -1}
            className={`absolute bottom-0 left-0 top-0 z-40 flex w-10 items-center justify-center bg-gradient-to-r from-[#141414] via-[#141414]/80 to-transparent text-white transition-all duration-300 md:w-14
              ${canLeft ? 'opacity-0 group-hover/row:opacity-100' : 'pointer-events-none opacity-0'}`}
          >
            <ChevronLeft className="h-9 w-9 drop-shadow transition-transform hover:scale-125" />
          </button>

          {/* Track */}
          <div
            ref={scrollRef}
            onScroll={measure}
            className="no-scrollbar flex items-center gap-2.5 overflow-x-auto scroll-smooth px-4 py-9 md:gap-3 md:px-12"
          >
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => <MovieCardSkeleton key={i} />)
              : movies.map((movie, i) =>
                  ranked && i < 10 ? (
                    <div key={movie.movieId} className="group relative flex flex-none items-end">
                      <span
                        aria-hidden
                        className="rank-number -mr-5 select-none text-[110px] sm:text-[150px] md:text-[190px]"
                      >
                        {i + 1}
                      </span>
                      <MovieCard
                        movie={movie}
                        onSelect={onSelectMovie}
                        onRate={onRateMovie}
                        userRating={userRatings[movie.movieId]}
                      />
                    </div>
                  ) : (
                    <MovieCard
                      key={movie.movieId}
                      movie={movie}
                      onSelect={onSelectMovie}
                      onRate={onRateMovie}
                      userRating={userRatings[movie.movieId]}
                    />
                  )
                )}
          </div>

          {/* Right arrow */}
          <button
            onClick={() => scroll('right')}
            aria-label={`Scroll ${title} right`}
            tabIndex={canRight ? 0 : -1}
            className={`absolute bottom-0 right-0 top-0 z-40 flex w-10 items-center justify-center bg-gradient-to-l from-[#141414] via-[#141414]/80 to-transparent text-white transition-all duration-300 md:w-14
              ${canRight ? 'opacity-0 group-hover/row:opacity-100' : 'pointer-events-none opacity-0'}`}
          >
            <ChevronRight className="h-9 w-9 drop-shadow transition-transform hover:scale-125" />
          </button>
        </div>
      </section>
    </Reveal>
  );
};
