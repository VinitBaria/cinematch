import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Film } from 'lucide-react';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Recommendations } from './pages/Recommendations';
import { Ratings } from './pages/Ratings';
import { Search } from './pages/Search';
import { Onboarding } from './pages/Onboarding';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const hideChrome = location.pathname === '/login' || location.pathname === '/register';

  // Jump to top on navigation
  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen flex-col bg-[#141414] font-sans text-[#e5e5e5]">
      {!hideChrome && <Navbar />}
      {/* Re-keyed on route so every page fades in */}
      <main key={location.pathname} className="flex-grow animate-fade-in">
        {children}
      </main>
      {!hideChrome && (
        <footer className="mt-10 border-t border-white/5 px-4 py-10 text-xs text-zinc-500 md:px-12">
          <div className="mx-auto flex max-w-[1800px] flex-col items-center justify-between gap-3 sm:flex-row">
            <div className="flex items-center gap-2">
              <Film className="h-4 w-4 text-[#e50914]" />
              <span className="font-display text-lg tracking-wider text-zinc-300">CINEMATCH AI</span>
              <span className="hidden sm:inline">· Recommendations powered by SVD matrix factorization</span>
            </div>
            <span className="font-mono text-emerald-500/80">RMSE 0.867</span>
          </div>
        </footer>
      )}
    </div>
  );
};

const NotFound: React.FC = () => (
  <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 text-center">
    <h1 className="font-display text-[9rem] leading-none text-gradient-red animate-fade-up md:text-[14rem]">404</h1>
    <h2 className="mb-3 text-2xl font-bold text-white animate-fade-up" style={{ animationDelay: '100ms' }}>
      Lost your way?
    </h2>
    <p className="mb-8 max-w-md text-zinc-400 animate-fade-up" style={{ animationDelay: '180ms' }}>
      Sorry, we can't find that film reel. There's plenty to watch on the home page.
    </p>
    <Link
      to="/"
      className="rounded-md bg-white px-7 py-3 text-sm font-bold text-black transition-all hover:bg-white/80 active:scale-95 animate-fade-up"
      style={{ animationDelay: '260ms' }}
    >
      Back to Home
    </Link>
  </div>
);

export const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/ratings" element={<Ratings />} />
            <Route path="/search" element={<Search />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
