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

export const GENRE_POSTERS: Record<string, string> = {
  Action: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80',
  Adventure: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80',
  Animation: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80',
  Comedy: 'https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=800&auto=format&fit=crop&q=80',
  Crime: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&auto=format&fit=crop&q=80',
  Drama: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80',
  Fantasy: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80',
  Horror: 'https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=800&auto=format&fit=crop&q=80',
  Romance: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80',
  'Sci-Fi': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80',
  Thriller: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&auto=format&fit=crop&q=80',
  Mystery: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&auto=format&fit=crop&q=80',
  Children: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80',
  Musical: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80',
  War: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80',
  Western: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&auto=format&fit=crop&q=80',
  Bollywood: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80',
  Hollywood: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80',
  Default: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80',
};

export const getMoviePoster = (m: AnyMovie): string => {
  const genres = m.genres || [];
  const firstGenre = genres[0] || 'Default';
  return GENRE_POSTERS[firstGenre] || GENRE_POSTERS.Default;
};

