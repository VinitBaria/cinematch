import React, { useState, useEffect } from 'react';
import {
  Film,
  PlusCircle,
  Sparkles,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
  Star,
  RefreshCw,
  Image as ImageIcon,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { Movie, MovieCreateInput } from '../types';

interface PresetMovie extends MovieCreateInput {
  starring?: string;
}

const BOLLYWOOD_PRESETS: PresetMovie[] = [
  {
    title: 'Jawan',
    year: 2023,
    industry: 'Bollywood',
    genres: ['Action', 'Thriller'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/jRtL02e5k4h1XGZ5d7N3C5s4Rk.jpg',
    overview: 'A prison warden mobilizes inmates to commit bold acts of justice that challenge systemic societal corruption.',
    avgRating: 4.8,
    ratingCount: 1540,
    starring: 'Shah Rukh Khan, Nayanthara',
  },
  {
    title: 'Stree 2',
    year: 2024,
    industry: 'Bollywood',
    genres: ['Comedy', 'Horror'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/uXygyfSTtKqL7QYlG2bN7D9c.jpg',
    overview: 'The town of Chanderi is haunted once more, this time by a headless entity named Sarkata that abducts modern progressive women.',
    avgRating: 4.7,
    ratingCount: 1120,
    starring: 'Rajkummar Rao, Shraddha Kapoor',
  },
  {
    title: 'Animal',
    year: 2023,
    industry: 'Bollywood',
    genres: ['Action', 'Crime', 'Drama'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/hr2qmC352zQ4QkX5m7Y1fX8B6.jpg',
    overview: 'A ruthless man wages total war against anyone who dares threaten his emotionally estranged father.',
    avgRating: 4.5,
    ratingCount: 1890,
    starring: 'Ranbir Kapoor, Anil Kapoor',
  },
  {
    title: '12th Fail',
    year: 2023,
    industry: 'Bollywood',
    genres: ['Drama'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/j9q3K2m7fB71eR2i6uPq8xY0c.jpg',
    overview: 'The inspiring true story of Manoj Kumar Sharma, who overcomes extreme poverty to clear the coveted UPSC civil services exam.',
    avgRating: 4.9,
    ratingCount: 2200,
    starring: 'Vikrant Massey, Medha Shankr',
  },
  {
    title: 'Pathaan',
    year: 2023,
    industry: 'Bollywood',
    genres: ['Action', 'Adventure', 'Thriller'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/m1b9toNW4UsH14g8O5nneW2g09e.jpg',
    overview: 'An exiled RAW agent teams up with a former ISI operative to take down a private terror syndicate planning biological warfare.',
    avgRating: 4.6,
    ratingCount: 1750,
    starring: 'Shah Rukh Khan, Deepika Padukone',
  },
  {
    title: 'RRR',
    year: 2022,
    industry: 'Bollywood',
    genres: ['Action', 'Drama', 'Adventure'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/nEufeZlyAOLqO2brrs0yeMu1Qje.jpg',
    overview: 'Two legendary Indian revolutionaries forge an unbreakable bond before fighting against the tyrannical British Raj.',
    avgRating: 4.9,
    ratingCount: 2800,
    starring: 'N.T. Rama Rao Jr., Ram Charan',
  },
  {
    title: '3 Idiots',
    year: 2009,
    industry: 'Bollywood',
    genres: ['Comedy', 'Drama'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/66A9MqXOyVFCssoloscw79z8Tew.jpg',
    overview: 'Two college friends search for their long-lost companion Rancho, revisiting memories of rebellion and genuine passion for learning.',
    avgRating: 5.0,
    ratingCount: 3100,
    starring: 'Aamir Khan, R. Madhavan, Sharman Joshi',
  },
  {
    title: 'Dangal',
    year: 2016,
    industry: 'Bollywood',
    genres: ['Drama'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/5kqq42aB6s4Qf5E2Y1x6nC3m2b.jpg',
    overview: 'Former wrestler Mahavir Singh Phogat trains his daughters Geeta and Babita to become world-class wrestling champions.',
    avgRating: 4.9,
    ratingCount: 2600,
    starring: 'Aamir Khan, Fatima Sana Shaikh',
  },
];

const HOLLYWOOD_PRESETS: PresetMovie[] = [
  {
    title: 'Oppenheimer',
    year: 2023,
    industry: 'Hollywood',
    genres: ['Drama', 'Thriller'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg',
    overview: 'The biographical saga of J. Robert Oppenheimer, the brilliant theoretical physicist who led the Manhattan Project.',
    avgRating: 4.9,
    ratingCount: 3400,
    starring: 'Cillian Murphy, Emily Blunt, Robert Downey Jr.',
  },
  {
    title: 'Dune: Part Two',
    year: 2024,
    industry: 'Hollywood',
    genres: ['Sci-Fi', 'Adventure', 'Action'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg',
    overview: 'Paul Atreides unites with Chani and the Fremen while seeking vengeance against the conspirators who destroyed his noble house.',
    avgRating: 4.9,
    ratingCount: 2900,
    starring: 'Timothée Chalamet, Zendaya, Rebecca Ferguson',
  },
  {
    title: 'Deadpool & Wolverine',
    year: 2024,
    industry: 'Hollywood',
    genres: ['Action', 'Comedy', 'Sci-Fi'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg',
    overview: 'A listless Wade Wilson is pulled out of civilian retirement by the TVA and teams up with a cynical Wolverine to save his universe.',
    avgRating: 4.8,
    ratingCount: 2450,
    starring: 'Ryan Reynolds, Hugh Jackman',
  },
  {
    title: 'Interstellar',
    year: 2014,
    industry: 'Hollywood',
    genres: ['Sci-Fi', 'Drama', 'Adventure'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
    overview: 'A team of intrepid explorers travels through a newly discovered wormhole in space to ensure humanity’s survival.',
    avgRating: 5.0,
    ratingCount: 4100,
    starring: 'Matthew McConaughey, Anne Hathaway, Jessica Chastain',
  },
  {
    title: 'The Dark Knight',
    year: 2008,
    industry: 'Hollywood',
    genres: ['Action', 'Crime', 'Drama'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
    overview: 'Batman raises the stakes in his war on crime with the help of Lt. Jim Gordon and DA Harvey Dent, until the Joker unleashes chaos.',
    avgRating: 5.0,
    ratingCount: 4500,
    starring: 'Christian Bale, Heath Ledger, Aaron Eckhart',
  },
  {
    title: 'Avatar: The Way of Water',
    year: 2022,
    industry: 'Hollywood',
    genres: ['Sci-Fi', 'Action', 'Adventure'],
    posterUrl: 'https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg',
    overview: 'Jake Sully lives with his newfound family on the extrasolar moon Pandora until a familiar threat returns to finish what was started.',
    avgRating: 4.7,
    ratingCount: 2100,
    starring: 'Sam Worthington, Zoe Saldaña, Sigourney Weaver',
  },
];

const AVAILABLE_GENRES = [
  'Action',
  'Adventure',
  'Animation',
  'Comedy',
  'Crime',
  'Drama',
  'Fantasy',
  'Horror',
  'Mystery',
  'Romance',
  'Sci-Fi',
  'Thriller',
];

const GENRE_FALLBACK_IMAGES: Record<string, string> = {
  Action: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80',
  Drama: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80',
  Comedy: 'https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=800&auto=format&fit=crop&q=80',
  Romance: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80',
  'Sci-Fi': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80',
  Thriller: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&auto=format&fit=crop&q=80',
  Horror: 'https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=800&auto=format&fit=crop&q=80',
  Adventure: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80',
  Bollywood: 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80',
  Hollywood: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80',
  Default: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80',
};

export const Admin: React.FC = () => {
  const [industryTab, setIndustryTab] = useState<'Bollywood' | 'Hollywood'>('Bollywood');
  const [recentMovies, setRecentMovies] = useState<Movie[]>([]);
  const [isLoadingRecent, setIsLoadingRecent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Form State
  const [title, setTitle] = useState('');
  const [year, setYear] = useState(2024);
  const [industry, setIndustry] = useState<'Bollywood' | 'Hollywood'>('Bollywood');
  const [selectedGenres, setSelectedGenres] = useState<string[]>(['Action', 'Drama']);
  const [posterUrl, setPosterUrl] = useState('');
  const [overview, setOverview] = useState('');
  const [avgRating, setAvgRating] = useState(4.8);
  const [ratingCount, setRatingCount] = useState(250);

  // Live preview image fallback
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    fetchRecentMovies();
  }, []);

  const fetchRecentMovies = async () => {
    try {
      setIsLoadingRecent(true);
      const data = await api.getRecentCustomMovies();
      setRecentMovies(data);
    } catch (err) {
      console.error('Failed to fetch custom movies', err);
    } finally {
      setIsLoadingRecent(false);
    }
  };

  const handleSelectPreset = (preset: PresetMovie) => {
    setTitle(preset.title);
    setYear(preset.year);
    setIndustry(preset.industry as 'Bollywood' | 'Hollywood');
    setSelectedGenres(preset.genres);
    setPosterUrl(preset.posterUrl || '');
    setOverview(preset.overview || '');
    setAvgRating(preset.avgRating || 4.8);
    setRatingCount(preset.ratingCount || 500);
    setImgError(false);
    setFeedback({
      type: 'success',
      message: `Selected preset "${preset.title}". Review or modify details below and click Add to Catalog.`,
    });
  };

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
  };

  const getEffectivePosterUrl = () => {
    if (posterUrl && !imgError) return posterUrl;
    const firstGenre = selectedGenres[0] || 'Default';
    return GENRE_FALLBACK_IMAGES[firstGenre] || GENRE_FALLBACK_IMAGES[industry] || GENRE_FALLBACK_IMAGES['Default'];
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setFeedback({ type: 'error', message: 'Movie title is required.' });
      return;
    }

    try {
      setIsSubmitting(true);
      setFeedback(null);

      const effectivePoster = getEffectivePosterUrl();

      const created = await api.createMovie({
        title: title.trim(),
        year: Number(year),
        genres: selectedGenres.length > 0 ? selectedGenres : ['Drama'],
        industry,
        posterUrl: effectivePoster,
        overview: overview.trim(),
        avgRating: Number(avgRating),
        ratingCount: Number(ratingCount),
      });

      setFeedback({
        type: 'success',
        message: `🎬 "${created.title}" successfully added! Live in the catalog and recommendation engine.`,
      });

      // Clear or reset fields
      setTitle('');
      setOverview('');
      setPosterUrl('');
      setImgError(false);
      fetchRecentMovies();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to add movie. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (movieId: number, movieTitle: string) => {
    if (!window.confirm(`Are you sure you want to remove "${movieTitle}"?`)) return;
    try {
      await api.deleteMovie(movieId);
      setFeedback({ type: 'success', message: `Movie "${movieTitle}" removed from catalog.` });
      fetchRecentMovies();
    } catch (err: any) {
      setFeedback({ type: 'error', message: 'Failed to delete movie.' });
    }
  };

  return (
    <div className="mx-auto min-h-screen max-w-[1700px] px-4 pt-24 pb-20 md:px-12">
      {/* Page Header */}
      <div className="mb-10 flex flex-col justify-between gap-4 border-b border-white/10 pb-6 md:flex-row md:items-end">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-400">
            <Zap className="h-3.5 w-3.5 text-red-400" />
            MLOps Catalog Studio
          </div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-white md:text-5xl">
            Movie Ingestion Studio
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-zinc-400 md:text-base">
            Add newly released <strong>Bollywood</strong> and <strong>Hollywood</strong> blockbusters to the live CineMatch AI catalog.
            Every film includes guaranteed HD posters, metadata, and automatic cold-start integration.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchRecentMovies}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-zinc-300 transition hover:bg-white/10"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoadingRecent ? 'animate-spin' : ''}`} />
            Refresh Catalog
          </button>
        </div>
      </div>

      {/* Feedback Toast */}
      {feedback && (
        <div
          className={`mb-8 flex items-center justify-between rounded-xl border p-4 text-sm font-medium ${
            feedback.type === 'success'
              ? 'border-emerald-500/30 bg-emerald-950/40 text-emerald-300'
              : 'border-red-500/30 bg-red-950/40 text-red-300'
          }`}
        >
          <div className="flex items-center gap-3">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-400" />
            )}
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-xs opacity-70 hover:opacity-100">
            Dismiss
          </button>
        </div>
      )}

      {/* ── 1. One-Click Blockbuster Presets ── */}
      <section className="mb-12 rounded-2xl border border-white/10 bg-white/[0.02] p-6 shadow-2xl backdrop-blur-md">
        <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-bold text-white">
              <Sparkles className="h-5 w-5 text-amber-400" />
              1-Click Blockbuster Presets
            </h2>
            <p className="text-xs text-zinc-400">
              Click any trending film to pre-populate all verified HD metadata and posters automatically.
            </p>
          </div>

          <div className="inline-flex rounded-lg bg-black/40 p-1 ring-1 ring-white/10">
            <button
              onClick={() => {
                setIndustryTab('Bollywood');
                setIndustry('Bollywood');
              }}
              className={`rounded-md px-4 py-1.5 text-xs font-semibold transition ${
                industryTab === 'Bollywood'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              🇮🇳 Bollywood Hits
            </button>
            <button
              onClick={() => {
                setIndustryTab('Hollywood');
                setIndustry('Hollywood');
              }}
              className={`rounded-md px-4 py-1.5 text-xs font-semibold transition ${
                industryTab === 'Hollywood'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              🎬 Hollywood Hits
            </button>
          </div>
        </div>

        {/* Preset Cards Grid */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-8">
          {(industryTab === 'Bollywood' ? BOLLYWOOD_PRESETS : HOLLYWOOD_PRESETS).map((p) => (
            <button
              key={p.title}
              onClick={() => handleSelectPreset(p)}
              className="group relative flex flex-col overflow-hidden rounded-xl border border-white/10 bg-zinc-900/60 p-2 text-left transition-all duration-300 hover:-translate-y-1 hover:border-red-500/50 hover:shadow-lg hover:shadow-red-950/30"
            >
              <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-zinc-800">
                <img
                  src={p.posterUrl}
                  alt={p.title}
                  loading="lazy"
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = GENRE_FALLBACK_IMAGES[p.genres[0]] || GENRE_FALLBACK_IMAGES.Default;
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <span className="absolute bottom-1.5 left-1.5 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-bold text-amber-300">
                  ★ {p.avgRating}
                </span>
              </div>
              <h3 className="mt-2 truncate text-xs font-bold text-white group-hover:text-red-400">
                {p.title}
              </h3>
              <p className="text-[10px] text-zinc-400">
                {p.year} · {p.genres[0]}
              </p>
            </button>
          ))}
        </div>
      </section>

      {/* ── 2. Movie Ingestion Form & Live Card Preview ── */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Form Column */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 shadow-xl backdrop-blur-md lg:col-span-8">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-white">
            <PlusCircle className="h-5 w-5 text-red-500" />
            Add Film to Catalog
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
              {/* Title */}
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  Movie Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jawan, Oppenheimer, Sholay"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 px-4 py-2.5 text-sm text-white placeholder-zinc-600 transition focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>

              {/* Release Year */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  Release Year *
                </label>
                <input
                  type="number"
                  required
                  min={1900}
                  max={2035}
                  value={year}
                  onChange={(e) => setYear(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 px-4 py-2.5 text-sm text-white transition focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>
            </div>

            {/* Industry Selection */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Industry / Cinema Category
              </label>
              <div className="mt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setIndustry('Bollywood')}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold transition ${
                    industry === 'Bollywood'
                      ? 'border-red-500 bg-red-600/20 text-white ring-1 ring-red-500'
                      : 'border-white/10 bg-white/5 text-zinc-400 hover:text-white'
                  }`}
                >
                  🇮🇳 Bollywood
                </button>
                <button
                  type="button"
                  onClick={() => setIndustry('Hollywood')}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold transition ${
                    industry === 'Hollywood'
                      ? 'border-red-500 bg-red-600/20 text-white ring-1 ring-red-500'
                      : 'border-white/10 bg-white/5 text-zinc-400 hover:text-white'
                  }`}
                >
                  🎬 Hollywood
                </button>
              </div>
            </div>

            {/* Genres Multi-select chips */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Genres (Select all that apply)
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {AVAILABLE_GENRES.map((g) => {
                  const active = selectedGenres.includes(g);
                  return (
                    <button
                      key={g}
                      type="button"
                      onClick={() => toggleGenre(g)}
                      className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                        active
                          ? 'bg-red-600 text-white shadow-sm'
                          : 'border border-white/10 bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-white'
                      }`}
                    >
                      {g}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Poster URL */}
            <div>
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  Poster Image URL
                </label>
                <span className="text-[11px] text-zinc-500">
                  Leave empty to auto-assign a high-res {industry} poster
                </span>
              </div>
              <div className="relative mt-1.5 flex items-center">
                <ImageIcon className="absolute left-3.5 h-4 w-4 text-zinc-500" />
                <input
                  type="url"
                  placeholder="https://image.tmdb.org/t/p/w500/... or any image link"
                  value={posterUrl}
                  onChange={(e) => {
                    setPosterUrl(e.target.value);
                    setImgError(false);
                  }}
                  className="w-full rounded-lg border border-white/10 bg-black/50 py-2.5 pr-4 pl-10 text-sm text-white placeholder-zinc-600 transition focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>
            </div>

            {/* Overview / Synopsis */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Synopsis / Plot Overview
              </label>
              <textarea
                rows={3}
                placeholder="Brief summary of the story, stars, and theme..."
                value={overview}
                onChange={(e) => setOverview(e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 p-3 text-sm text-white placeholder-zinc-600 transition focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              />
            </div>

            {/* Initial Rating Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  Critic / Initial Rating (0.5 – 5.0)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="5.0"
                  value={avgRating}
                  onChange={(e) => setAvgRating(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 px-4 py-2 text-sm text-white focus:border-red-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  Initial Review Count
                </label>
                <input
                  type="number"
                  min="1"
                  value={ratingCount}
                  onChange={(e) => setRatingCount(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 px-4 py-2 text-sm text-white focus:border-red-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 py-3 text-sm font-bold text-white shadow-lg transition hover:bg-red-500 active:scale-[0.99] disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Saving to Live Catalog...
                </>
              ) : (
                <>
                  <PlusCircle className="h-4 w-4" />
                  Publish Movie to CineMatch AI
                </>
              )}
            </button>
          </form>
        </div>

        {/* Live Preview Column */}
        <div className="lg:col-span-4">
          <div className="sticky top-24 rounded-2xl border border-white/10 bg-white/[0.02] p-6 shadow-xl backdrop-blur-md">
            <h3 className="mb-4 flex items-center justify-between text-sm font-bold tracking-wider text-zinc-400 uppercase">
              <span>Live Card Preview</span>
              <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                Guaranteed Poster
              </span>
            </h3>

            {/* CineMatch Card Simulation */}
            <div className="mx-auto max-w-[280px] overflow-hidden rounded-xl border border-white/10 bg-zinc-900 shadow-2xl">
              <div className="relative aspect-[2/3] w-full overflow-hidden bg-zinc-800">
                <img
                  src={getEffectivePosterUrl()}
                  alt={title || 'Preview'}
                  className="h-full w-full object-cover"
                  onError={() => setImgError(true)}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-80" />

                <div className="absolute top-2.5 left-2.5">
                  <span className="rounded bg-red-600 px-2 py-0.5 text-[10px] font-black tracking-wide text-white uppercase">
                    {industry}
                  </span>
                </div>

                <div className="absolute right-2.5 bottom-2.5 flex items-center gap-1 rounded bg-black/80 px-2 py-1 text-xs font-bold text-amber-400">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  {avgRating.toFixed(1)}
                </div>
              </div>

              <div className="p-4">
                <h4 className="truncate text-base font-bold text-white">
                  {title || 'Movie Title'}
                </h4>
                <div className="mt-1 flex items-center gap-2 text-xs text-zinc-400">
                  <span>{year}</span>
                  <span>•</span>
                  <span className="truncate">{selectedGenres.join(', ') || 'Genres'}</span>
                </div>
                <p className="mt-2.5 line-clamp-2 text-xs text-zinc-400">
                  {overview || 'Synopsis and plot summary will appear here for browsing users.'}
                </p>
              </div>
            </div>

            <div className="mt-5 rounded-lg border border-white/5 bg-black/40 p-3 text-xs text-zinc-400">
              <p className="flex items-center gap-1.5 font-semibold text-zinc-300">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Poster Reliability Guarantee:
              </p>
              <p className="mt-1 text-[11px] text-zinc-500">
                If custom image links fail or are blocked by browser CORS, our system automatically falls back to an HD curated studio poster.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── 3. Manage Ingested Custom Movies ── */}
      <section className="mt-16">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-2xl font-bold text-white">
              <Layers className="h-6 w-6 text-red-500" />
              Recently Ingested Movies ({recentMovies.length})
            </h2>
            <p className="text-xs text-zinc-400">
              Custom titles added via this admin panel. They are instantly searchable and part of recommendation pipelines.
            </p>
          </div>
        </div>

        {recentMovies.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.01] p-12 text-center">
            <Film className="mx-auto h-12 w-12 text-zinc-600" />
            <p className="mt-3 text-sm font-semibold text-zinc-300">No custom movies added yet</p>
            <p className="mt-1 text-xs text-zinc-500">
              Use the presets above or form to add newly released Bollywood and Hollywood titles.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {recentMovies.map((m) => (
              <div
                key={m.movieId}
                className="flex gap-4 rounded-xl border border-white/10 bg-white/[0.02] p-3 shadow-lg transition hover:border-white/20"
              >
                <img
                  src={m.posterUrl || GENRE_FALLBACK_IMAGES.Default}
                  alt={m.title}
                  className="h-28 w-20 flex-shrink-0 rounded-lg object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = GENRE_FALLBACK_IMAGES.Default;
                  }}
                />
                <div className="flex flex-1 flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between gap-1">
                      <h3 className="line-clamp-1 text-sm font-bold text-white" title={m.title}>
                        {m.title}
                      </h3>
                      <button
                        onClick={() => handleDelete(m.movieId, m.title)}
                        className="text-zinc-500 transition hover:text-red-400"
                        title="Delete from catalog"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <p className="text-[11px] text-zinc-400">
                      {m.year} · {m.industry || 'Catalog'}
                    </p>
                    <p className="mt-1 line-clamp-1 text-[11px] text-red-400">
                      {m.genres?.slice(0, 2).join(', ')}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-xs text-zinc-500">
                    <span className="flex items-center gap-1 font-bold text-amber-400">
                      ★ {m.avgRating?.toFixed(1) || '4.5'}
                    </span>
                    <span className="font-mono text-[10px]">ID: {m.movieId}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Admin;
