// Owner: Person B
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { LogIn, AlertCircle, Train } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.login({ email, password });
      const next = new URLSearchParams(window.location.search).get('next');
      if (next?.startsWith('/') && !next.startsWith('//') && !next.includes('\\')) {
        router.push(next);
      } else if (res.user.role === 'ADMIN') {
        router.push('/admin');
      } else {
        router.push('/search');
      }
    } catch (err: any) {
      setError(err?.error?.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg border border-slate-200 p-8">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-railway-navy text-railway-gold rounded-xl mb-3 shadow">
            <Train className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Sign in to Tatkal Express</h2>
          <p className="text-sm text-slate-600 mt-1">Book general and high-demand Tatkal railway tickets</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. chiranth@example.com"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-railway-blue text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-railway-blue text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-railway-navy hover:bg-slate-800 text-white rounded-lg font-semibold text-sm transition flex items-center justify-center gap-2 shadow disabled:opacity-50"
          >
            {loading ? (
              <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-slate-200 text-center text-xs text-slate-600">
          Don't have an account?{' '}
          <Link href="/register" className="font-semibold text-railway-blue hover:underline">
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
}
