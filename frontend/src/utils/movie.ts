import { Movie, RecommendationItem } from '../types';

export type AnyMovie = Movie | RecommendationItem;

export const isRecommendation = (m: AnyMovie): m is RecommendationItem =>
  'predictedRating' in m && (m as RecommendationItem).predictedRating !== undefined;

export const displayTitle = (m: AnyMovie) => m.cleanTitle || m.title;

export const displayYear = (m: AnyMovie) => (m.year ? Math.round(m.year) : null);

/** "98% Match" style score derived from the SVD prediction or the community average. */
export const matchPercent = (m: AnyMovie): number | null => {
  if (isRecommendation(m) && m.predictedRating) {
    return Math.max(60, Math.min(99, Math.round((m.predictedRating / 5) * 100)));
  }
  if (m.avgRating) {
    return Math.max(60, Math.min(98, Math.round((m.avgRating / 5) * 100)));
  }
  return null;
};

/** Deterministic gradient so posters without artwork still look intentional. */
export const posterGradient = (seed: string): string => {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  const hue = h % 360;
  return `linear-gradient(145deg, hsl(${hue} 55% 22%) 0%, hsl(${(hue + 40) % 360} 60% 10%) 100%)`;
};

export const RATING_LABELS: Record<number, string> = {
  1: 'Hated it',
  2: "Didn't like it",
  3: "It's okay",
  4: 'Liked it',
  5: 'Loved it!',
};
