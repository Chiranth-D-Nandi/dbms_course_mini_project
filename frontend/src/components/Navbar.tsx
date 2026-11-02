// Owner: Person B
'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { User } from '@/lib/types';
import { Train, Shield, HelpCircle, Ticket, LogIn, LogOut, User as UserIcon, Phone, Clock, Search, ShieldCheck } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    setUser(api.getCurrentUser());
  }, [pathname]);

  // Live IST Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone: 'Asia/Kolkata',
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      };
      setCurrentTime(now.toLocaleDateString('en-IN', options));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    api.clearTokens();
    setUser(null);
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-50 shadow-md">
      {/* Top Official Government / IRCTC Utility Strip */}
      <div className="bg-[#0a192f] text-slate-300 text-[11px] py-1 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-200 tracking-wide uppercase">
              भारतीय रेल &bull; Indian Railways
            </span>
            <span className="hidden md:inline text-slate-600">|</span>
            <span className="hidden md:inline text-slate-400">
              Centre for Railway Information Systems (CRIS)
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="hidden sm:flex items-center gap-1 text-amber-400 font-mono text-[11px]">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>{currentTime || 'IST Live Time'}</span>
            </div>
            <a
              href="tel:139"
              className="flex items-center gap-1 text-slate-300 hover:text-white transition"
              title="24x7 Customer Grievance & Information"
            >
              <Phone className="w-3 h-3 text-emerald-400" />
              <span className="font-bold text-[11px]">Rail Madad: 139</span>
            </a>
          </div>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="bg-[#0f2e5a] text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="bg-amber-500 group-hover:bg-amber-400 p-2.5 rounded-xl text-[#0f2e5a] shadow transition flex items-center justify-center">
              <Train className="w-6 h-6 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 leading-none">
                <span className="font-black text-xl tracking-tight text-white">TATKAL</span>
                <span className="font-black text-xl tracking-tight text-amber-400">EXPRESS</span>
                <span className="hidden lg:inline-block text-[9px] bg-amber-400/20 text-amber-300 font-bold px-1.5 py-0.5 rounded ml-1 border border-amber-400/30 uppercase tracking-wider">
                  NextGen
                </span>
              </div>
              <span className="block text-[11px] text-slate-300 tracking-wide mt-1 font-medium">
                National Train Reservation & Tatkal Portal
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-3">
            <Link
              href="/search"
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition flex items-center gap-1.5 ${
                pathname === '/search'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-200 hover:bg-white/10 hover:text-white'
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Book Tickets</span>
            </Link>

            <Link
              href="/help"
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition flex items-center gap-1.5 ${
                pathname === '/help'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-200 hover:bg-white/10 hover:text-white'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Tatkal Rules & FAQ</span>
              <span className="sm:hidden">Rules</span>
            </Link>

            {user && (
              <Link
                href="/bookings"
                className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition flex items-center gap-1.5 ${
                  pathname.startsWith('/bookings')
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Ticket className="w-4 h-4 text-amber-300" />
                <span>My Bookings</span>
              </Link>
            )}

            {user?.role === 'ADMIN' && (
              <Link
                href="/admin"
                className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition flex items-center gap-1.5 ${
                  pathname.startsWith('/admin')
                    ? 'bg-red-700 text-white shadow-xs'
                    : 'text-amber-300 hover:bg-white/10'
                }`}
              >
                <Shield className="w-4 h-4" />
                <span>Admin Portal</span>
              </Link>
            )}

            {/* Auth Section */}
            {user ? (
              <div className="flex items-center space-x-2 ml-2 pl-3 border-l border-white/20">
                <div className="hidden md:flex flex-col text-right">
                  <span className="text-xs font-bold text-white flex items-center gap-1 justify-end">
                    <UserIcon className="w-3.5 h-3.5 text-amber-400" />
                    {user.first_name}
                  </span>
                  <span className="text-[10px] text-amber-300 font-semibold uppercase tracking-wider">
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Sign out"
                  className="flex items-center space-x-1 text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-600 transition"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline font-medium">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 ml-2 pl-3 border-l border-white/20">
                <Link
                  href="/login"
                  className="flex items-center space-x-1.5 text-xs sm:text-sm bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-3.5 py-1.5 rounded-lg transition shadow"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Login</span>
                </Link>
                <Link
                  href="/register"
                  className="hidden sm:inline-block text-xs font-semibold text-slate-200 hover:text-white px-2 py-1.5 transition"
                >
                  Register
                </Link>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
