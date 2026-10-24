export interface Movie {
  movieId: number;
  title: string;
  cleanTitle?: string;
  year?: number;
  genres: string[];
  industry?: string;
  isCustom?: boolean;
  posterUrl?: string;
  overview?: string;
  tmdbId?: number;
  avgRating?: number;
  ratingCount?: number;
  userRating?: number;
}

export interface MovieCreateInput {
  title: string;
  year: number;
  genres: string[];
  industry: 'Bollywood' | 'Hollywood' | string;
  overview?: string;
  posterUrl?: string;
  avgRating?: number;
  ratingCount?: number;
}

export interface MovieListResponse {
  movies: Movie[];
  total: number;
  page: number;
  pageSize: number;
}

export interface Rating {
  userId: number;
  movieId: number;
  rating: number;
  title?: string;
  posterUrl?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface RecommendationItem {
  movieId: number;
  title: string;
  cleanTitle?: string;
  year?: number;
  genres: string[];
  posterUrl?: string;
  overview?: string;
  tmdbId?: number;
  predictedRating?: number;
  popularityScore?: number;
  avgRating?: number;
  ratingCount?: number;
  recommendationStrategy: 'svd_matrix_factorization' | 'neighbor_collaborative_filtering' | 'popularity_bayesian_weighted' | string;
  modelVersion?: string;
}

export interface RecommendationResponse {
  recommendations: RecommendationItem[];
  strategy: string;
  modelVersion?: string;
  userId: number;
}

export interface User {
  userId: number;
  name: string;
  email: string;
  ratingCount?: number;
  createdAt?: string;
}

export interface AuthResponse {
  userId: number;
  name: string;
  email: string;
  token: string;
}

export interface ModelInfo {
  modelVersion: string;
  algorithm: string;
  parameters: {
    n_factors?: number;
    lr_all?: number;
    reg_all?: number;
    n_epochs?: number;
    [key: string]: any;
  };
  trainsetStats: {
    n_users?: number;
    n_items?: number;
    n_ratings?: number;
    rating_scale?: [number, number];
  };
  trainedAt: string;
  knownUsers: number;
  knownMovies: number;
}
