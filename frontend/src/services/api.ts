import axios from 'axios';
import {
  Movie,
  MovieListResponse,
  Rating,
  RecommendationResponse,
  User,
  AuthResponse,
  ModelInfo,
} from '../types';

const API_BASE = '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to requests if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('cinematch_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for handling 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // If unauthorized, clear token if stored
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        localStorage.removeItem('cinematch_token');
        localStorage.removeItem('cinematch_user');
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // ── Authentication ──
  async login(credentials: { email: string; password: string }): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return data;
  },

  async register(details: { name: string; email: string; password: string }): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>('/auth/register', details);
    return data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // ignore
    } finally {
      localStorage.removeItem('cinematch_token');
      localStorage.removeItem('cinematch_user');
    }
  },

  async getMe(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },

  // ── Movies ──
  async getMovies(params: {
    page?: number;
    page_size?: number;
    genre?: string;
    year_min?: number;
    year_max?: number;
    sort_by?: string;
  } = {}): Promise<MovieListResponse> {
    const { data } = await apiClient.get<MovieListResponse>('/movies', { params });
    return data;
  },

  async searchMovies(query: string, limit = 20): Promise<Movie[]> {
    if (!query.trim()) return [];
    const { data } = await apiClient.get<Movie[]>('/movies/search', {
      params: { query, limit },
    });
    return data;
  },

  async getTrending(limit = 15): Promise<Movie[]> {
    const { data } = await apiClient.get<Movie[]>('/movies/trending', {
      params: { limit },
    });
    return data;
  },

  async getPopular(limit = 15): Promise<Movie[]> {
    const { data } = await apiClient.get<Movie[]>('/movies/popular', {
      params: { limit },
    });
    return data;
  },

  async getTopRated(limit = 15): Promise<Movie[]> {
    const { data } = await apiClient.get<Movie[]>('/movies/top-rated', {
      params: { limit },
    });
    return data;
  },

  async getOnboardingPicks(limit = 24): Promise<Movie[]> {
    const { data } = await apiClient.get<Movie[]>('/movies/onboarding-picks', {
      params: { limit },
    });
    return data;
  },

  async getMovieById(movieId: number): Promise<Movie> {
    const { data } = await apiClient.get<Movie>(`/movies/${movieId}`);
    return data;
  },

  // ── Ratings ──
  async submitRating(movieId: number, rating: number): Promise<Rating> {
    const { data } = await apiClient.post<Rating>('/ratings', { movieId, rating });
    return data;
  },

  async getUserRatings(limit = 100, skip = 0): Promise<Rating[]> {
    const { data } = await apiClient.get<Rating[]>('/ratings', {
      params: { limit, skip },
    });
    return data;
  },

  async deleteRating(movieId: number): Promise<void> {
    await apiClient.delete(`/ratings/${movieId}`);
  },

  // ── Recommendations ──
  async getRecommendations(limit = 15): Promise<RecommendationResponse> {
    const { data } = await apiClient.get<RecommendationResponse>('/recommendations', {
      params: { limit },
    });
    return data;
  },

  async getColdStartRecommendations(limit = 15): Promise<RecommendationResponse> {
    const { data } = await apiClient.get<RecommendationResponse>('/recommendations/cold-start', {
      params: { limit },
    });
    return data;
  },

  // ── System & ML Info ──
  async getHealth(): Promise<any> {
    const { data } = await apiClient.get('/health');
    return data;
  },

  async getModelInfo(): Promise<ModelInfo> {
    const { data } = await apiClient.get<ModelInfo>('/model/info');
    return data;
  },
};
