// Owner: Person B
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Play, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AdminRunsPage() {
  const [runIdInput, setRunIdInput] = useState('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateInventory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!runIdInput) return;

    setLoading(true);
    setStatusMsg(null);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/admin/runs/${runIdInput}/generate-inventory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('tatkal_access_token') || ''}`,
        },
      });
      const data = await res.json();
      if (!res.ok) throw data;
      setStatusMsg(`Successfully executed sp_generate_run_inventory(${runIdInput}): ${data.message || 'Inventory populated!'}`);
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
          <h1 className="text-xl font-bold text-slate-900">Run Inventory Generator</h1>
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
              Run ID
            </label>
            <input
              type="number"
              required
              value={runIdInput}
              onChange={(e) => setRunIdInput(e.target.value)}
              placeholder="e.g. 101"
              className="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:ring-2 focus:ring-railway-blue focus:outline-none"
            />
          </div>

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
                <span>Execute sp_generate_run_inventory</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
