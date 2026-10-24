import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PosterWall } from '../components/PosterWall';
import { Field } from '../components/Field';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setIsLoading(true);
    try {
      await register(name, email, password);
      navigate('/onboarding');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Email may already be in use.');
    } finally {
      setIsLoading(false);
    }
  };

  // Tiny strength meter for the password field
  const strength = Math.min(
    4,
    (password.length >= 6 ? 1 : 0) +
      (password.length >= 10 ? 1 : 0) +
      (/[A-Z]/.test(password) && /[a-z]/.test(password) ? 1 : 0) +
      (/\d/.test(password) || /[^A-Za-z0-9]/.test(password) ? 1 : 0)
  );
  const strengthColors = ['bg-white/10', 'bg-red-500', 'bg-orange-500', 'bg-yellow-400', 'bg-emerald-500'];

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
        <h1 className="mb-1 text-3xl font-bold text-white">Create Account</h1>
        <p className="mb-7 text-sm text-zinc-400">Rate a few films and we'll do the rest.</p>

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
          <Field label="Your name" autoComplete="name" required value={name} onChange={setName} />
          <Field label="Email" type="email" autoComplete="email" required value={email} onChange={setEmail} />
          <div>
            <Field
              label="Password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={setPassword}
            />
            <div className="mt-2 flex gap-1.5" aria-hidden>
              {[1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                    i <= strength ? strengthColors[strength] : 'bg-white/10'
                  }`}
                />
              ))}
            </div>
          </div>
          <Field
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={setConfirmPassword}
          />

          <button
            type="submit"
            disabled={isLoading}
            className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-[#e50914] text-base font-bold text-white transition-all hover:bg-[#f6121d] active:scale-[0.98] disabled:opacity-60"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Get Started'}
          </button>
        </form>

        <p className="mt-7 text-sm text-zinc-400">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-white hover:underline">
            Sign in
          </Link>
          .
        </p>
      </div>
    </div>
  );
};
