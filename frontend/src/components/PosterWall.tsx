import React, { useMemo } from 'react';
import { Film } from 'lucide-react';
import { posterGradient } from '../utils/movie';

/** Pure-CSS animated wall of poster tiles — a cinematic backdrop with zero network requests. */
export const PosterWall: React.FC = () => {
  const columns = useMemo(
    () =>
      Array.from({ length: 7 }).map((_, c) =>
        Array.from({ length: 8 }).map((_, r) => `tile-${c}-${r}-${(c * 7 + r * 3) % 11}`)
      ),
    []
  );

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden bg-black" aria-hidden>
      <div className="absolute -inset-[20%] flex -rotate-[14deg] justify-center gap-4 opacity-60">
        {columns.map((tiles, c) => (
          <div key={c} className="w-36 flex-none sm:w-44" style={{ marginTop: c % 2 ? '-6rem' : '0' }}>
            <div className={c % 2 ? 'animate-wall-down' : 'animate-wall-up'}>
              {[...tiles, ...tiles].map((seed, i) => (
                <div
                  key={i}
                  className="mb-4 flex aspect-[2/3] w-full items-center justify-center rounded-md ring-1 ring-white/10"
                  style={{ background: posterGradient(seed) }}
                >
                  <Film className="h-6 w-6 text-white/15" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/70 to-black/80" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,black_75%)]" />
      <div className="absolute -top-40 left-1/2 h-96 w-[60rem] -translate-x-1/2 rounded-full bg-[#e50914]/25 blur-[120px]" />
    </div>
  );
};
