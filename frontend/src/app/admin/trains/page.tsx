// Owner: Person B
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ArrowLeft, Train, Plus } from 'lucide-react';

export default function AdminTrainsPage() {
  const [trains, setTrains] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Search trains or fetch all
    api
      .listTrains()
      .then(setTrains)
      .catch(() => setTrains([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex justify-between items-center">
        <Link
          href="/admin"
          className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
        </Link>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Manage Rolling Stock & Train Profiles</h1>
            <p className="text-xs text-slate-500">Browse train routes and coaches; schedule departures from Train Runs.</p>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading trains catalog...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {trains.map((t, idx) => (
              <div key={idx} className="p-4 border border-slate-200 rounded-lg bg-slate-50/50 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-900 text-sm">{t.train_name}</span>
                  <span className="font-mono text-xs font-bold bg-slate-200 px-2 py-0.5 rounded">
                    #{t.train_number}
                  </span>
                </div>
                <div className="text-xs text-slate-500">
                  Origin: <span className="font-semibold text-slate-700">{t.origin_code}</span> &rarr; Destination: <span className="font-semibold text-slate-700">{t.destination_code}</span>
                </div>
                <div className="flex justify-between items-center pt-2 text-[11px] border-t border-slate-200">
                  <span className="text-slate-500">Type: {t.train_type}</span>
                  <Link
                    href={`/trains/${t.train_id}`}
                    className="text-railway-blue font-bold hover:underline"
                  >
                    View Timetable &rarr;
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
