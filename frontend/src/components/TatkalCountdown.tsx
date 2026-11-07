// Owner: Person B
'use client';

import { useState, useEffect } from 'react';
import { Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface Props {
  secondsRemaining: number;
  isOpen: boolean;
  tatkalOpenTime: string;
  onWindowOpen?: () => void;
}

export default function TatkalCountdown({
  secondsRemaining,
  isOpen,
  tatkalOpenTime,
  onWindowOpen,
}: Props) {
  const [timeLeft, setTimeLeft] = useState(secondsRemaining);

  useEffect(() => {
    setTimeLeft(secondsRemaining);
  }, [secondsRemaining]);

  useEffect(() => {
    const interval = setInterval(() => setTimeLeft(prev => Math.max(0, prev - 1)), 1000);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    if (!isOpen && secondsRemaining > 0 && timeLeft === 0) onWindowOpen?.();
  }, [timeLeft, isOpen, secondsRemaining, onWindowOpen]);

  const hours = Math.floor(timeLeft / 3600);
  const minutes = Math.floor((timeLeft % 3600) / 60);
  const seconds = timeLeft % 60;

  if (isOpen) {
    return (
      <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-4 flex items-center justify-between text-emerald-900 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 rounded-lg text-emerald-700">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm">Tatkal Booking Window is OPEN</h4>
            <p className="text-xs text-emerald-700">High-concurrency allocation active &bull; Seats subject to rapid sell-out</p>
          </div>
        </div>
        <span className="bg-emerald-200 text-emerald-900 text-xs font-mono font-bold px-2.5 py-1 rounded uppercase">
          LIVE
        </span>
      </div>
    );
  }

  return (
    <div className="bg-red-50 border border-red-300 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-red-900 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-red-100 rounded-lg text-red-600">
          <Clock className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <h4 className="font-bold text-sm">Tatkal Booking Window Opens Soon</h4>
          <p className="text-xs text-red-700">
            Window opens at {new Date(tatkalOpenTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}. Prepare passenger details now!
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 font-mono">
        <div className="bg-white border border-red-200 rounded px-2.5 py-1 text-center shadow-inner">
          <span className="block text-lg font-black text-red-700">{String(hours).padStart(2, '0')}</span>
          <span className="block text-[9px] uppercase text-slate-500 font-sans">Hrs</span>
        </div>
        <span className="font-bold text-red-400">:</span>
        <div className="bg-white border border-red-200 rounded px-2.5 py-1 text-center shadow-inner">
          <span className="block text-lg font-black text-red-700">{String(minutes).padStart(2, '0')}</span>
          <span className="block text-[9px] uppercase text-slate-500 font-sans">Min</span>
        </div>
        <span className="font-bold text-red-400">:</span>
        <div className="bg-white border border-red-200 rounded px-2.5 py-1 text-center shadow-inner">
          <span className="block text-lg font-black text-red-700">{String(seconds).padStart(2, '0')}</span>
          <span className="block text-[9px] uppercase text-slate-500 font-sans">Sec</span>
        </div>
      </div>
    </div>
  );
}
