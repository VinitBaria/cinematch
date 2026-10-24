import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, UserCheck, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PosterWall } from '../components/PosterWall';
import { Field } from '../components/Field';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, demoLogin } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemo = async (type: 'svd' | 'new') => {
    setError(null);
    setIsLoading(true);
    try {
      await demoLogin(type);
      navigate(type === 'svd' ? '/recommendations' : '/onboarding');
    } catch {
      setError('Demo login failed. Make sure the backend is running and the database is seeded.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grain relative flex min-h-screen w-full items-center justify-center px-4 py-16">
      <PosterWall />

      <Link
        to="/"
        className="absolute left-5 top-5 z-20 font-display text-3xl tracking-wider text-[#e50914] transition-all hover:drop-shadow-[0_0_14px_rgba(229,9,20,0.7)] md:left-12 md:top-8 md:text-5xl"
      >
        CINEMATCH
      </Link>

      <div className="relative z-10 w-full max-w-[28rem] rounded-xl bg-black/75 p-8 shadow-2xl shadow-black ring-1 ring-white/10 backdrop-blur-xl animate-scale-in sm:p-12">
        <h1 className="mb-1 text-3xl font-bold text-white">Sign In</h1>
        <p className="mb-7 text-sm text-zinc-400">Pick up where you left off.</p>

        {error && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-2.5 rounded-md bg-[#e87c03]/15 p-3 text-sm text-orange-200 ring-1 ring-orange-500/30 animate-fade-down"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-orange-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Email" type="email" autoComplete="email" required value={email} onChange={setEmail} />
          <Field
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={setPassword}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-[#e50914] text-base font-bold text-white transition-all hover:bg-[#f6121d] active:scale-[0.98] disabled:opacity-60"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Sign In'}
          </button>
        </form>

        {/* Demo accounts */}
        <div className="mt-7">
          <div className="mb-3 flex items-center gap-3 text-[11px] font-bold uppercase tracking-widest text-zinc-500">
            <span className="h-px flex-1 bg-white/10" />
            Try a demo
            <span className="h-px flex-1 bg-white/10" />
          </div>
          <div className="grid gap-2">
            <DemoButton
              onClick={() => handleDemo('svd')}
              disabled={isLoading}
              icon={<Sparkles className="h-4 w-4 text-[#e50914]" />}
              title="Pre-trained Cinephile"
              desc="200+ ratings · full AI picks"
            />
            <DemoButton
              onClick={() => handleDemo('new')}
              disabled={isLoading}
              icon={<UserCheck className="h-4 w-4 text-emerald-400" />}
              title="Fresh Cold-Start Account"
              desc="Zero ratings · try onboarding"
            />
          </div>
        </div>

        <p className="mt-7 text-sm text-zinc-400">
          New to CineMatch?{' '}
          <Link to="/register" className="font-semibold text-white hover:underline">
            Sign up now
          </Link>
          .
        </p>
      </div>
    </div>
  );
};

const DemoButton: React.FC<{
  onClick: () => void;
  disabled?: boolean;
  icon: React.ReactNode;
  title: string;
  desc: string;
}> = ({ onClick, disabled, icon, title, desc }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className="group flex items-center justify-between rounded-md bg-white/5 px-4 py-3 text-left ring-1 ring-white/10 transition-all hover:bg-white/10 hover:ring-white/25 disabled:opacity-50"
  >
    <span className="flex items-center gap-3">
      {icon}
      <span>
        <span className="block text-sm font-semibold text-white">{title}</span>
        <span className="block text-xs text-zinc-400">{desc}</span>
      </span>
    </span>
    <ArrowRight className="h-4 w-4 text-zinc-500 transition-all group-hover:translate-x-1 group-hover:text-white" />
  </button>
);
