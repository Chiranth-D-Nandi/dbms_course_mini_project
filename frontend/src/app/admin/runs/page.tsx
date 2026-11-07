// Owner: Person B
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Play, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '@/lib/api';

export default function AdminRunsPage() {
  const [runIdInput, setRunIdInput] = useState('');
  const [journeyDate, setJourneyDate] = useState('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateInventory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!runIdInput) return;

    setLoading(true);
    setStatusMsg(null);

    try {
      const data = await api.createRun(Number(runIdInput), journeyDate);
      setStatusMsg(data.message);
    } catch (err: any) {
      setStatusMsg(`Error: ${err?.error?.message || err?.message || 'Failed to generate inventory'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <Link
        href="/admin"
        className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
      </Link>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Schedule a train run</h1>
          <p className="text-xs text-slate-500">
            Invokes MySQL Stored Procedure <code>sp_generate_run_inventory(run_id)</code> to populate <code>run_seat</code> inventory table and set Tatkal quota allocations.
          </p>
        </div>

        {statusMsg && (
          <div className={`p-3 rounded-lg text-xs font-medium ${
            statusMsg.startsWith('Error') ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
          }`}>
            {statusMsg}
          </div>
        )}

        <form onSubmit={handleGenerateInventory} className="max-w-md space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Train ID
            </label>
            <input
              type="number"
              min="1"
              required
              value={runIdInput}
              onChange={(e) => setRunIdInput(e.target.value)}
              placeholder="e.g. 101"
              className="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-railway-blue focus:outline-none"
            />
          </div>
          <label className="block text-sm">Journey date<input aria-label="Journey date" type="date" required value={journeyDate} min={new Date().toISOString().slice(0,10)} onChange={e => setJourneyDate(e.target.value)} className="mt-1 block w-full rounded border p-2"/></label>

          <button
            type="submit"
            disabled={loading}
            className="py-2.5 px-4 bg-railway-navy hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition flex items-center gap-2 shadow disabled:opacity-50"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Play className="w-4 h-4 text-railway-gold" />
                <span>Create run and inventory</span>
              </>
            )}
          </button>
        </form>
        <button type="button" disabled={loading} className="text-sm font-bold text-blue-700" onClick={async () => {setLoading(true); try {const result = await api.releaseHolds(); setStatusMsg(result.message);} catch(e: any) {setStatusMsg(`Error: ${e?.error?.message || 'Hold sweep failed'}`);} finally {setLoading(false);}}}>Release expired holds now</button>
      </div>
    </div>
  );
}
