// Owner: Person B
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ArrowLeft, Activity, ShieldCheck, RefreshCw } from 'lucide-react';

export default function AdminAuditLogPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = () => {
    setLoading(true);
    api
      .getAdminAuditLog()
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
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
        <button
          onClick={fetchLogs}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1 transition"
        >
          <RefreshCw className="w-3 h-3" /> Refresh Logs
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-red-600" />
            <h1 className="text-xl font-bold text-slate-900">Database Trigger Audit Trail (audit_log)</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Immutable log written exclusively by MySQL triggers (<code>trg_booking_status_audit</code>, <code>trg_run_seat_audit</code>) capturing before/after JSON diffs.
          </p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">Loading trigger logs...</div>
        ) : logs.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No audit log entries recorded yet. Book tickets or update seat states to observe trigger executions.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                  <th className="pb-2">Log ID</th>
                  <th className="pb-2">Table</th>
                  <th className="pb-2">Record ID</th>
                  <th className="pb-2">Action</th>
                  <th className="pb-2">State Diff (Old &rarr; New JSON)</th>
                  <th className="pb-2 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-slate-50">
                    <td className="py-2.5 font-mono">{log.log_id}</td>
                    <td className="py-2.5 font-bold text-slate-800">{log.table_name}</td>
                    <td className="py-2.5 font-mono text-slate-600">#{log.record_id}</td>
                    <td className="py-2.5">
                      <span className="bg-blue-50 text-blue-800 font-bold px-1.5 py-0.5 rounded text-[10px]">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2.5 font-mono text-[11px] max-w-md">
                      <div className="bg-slate-50 p-2 rounded border border-slate-200 space-y-1">
                        {log.old_value && (
                          <div className="text-red-700">
                            <span className="font-bold">OLD: </span>
                            {typeof log.old_value === 'string' ? log.old_value : JSON.stringify(log.old_value)}
                          </div>
                        )}
                        {log.new_value && (
                          <div className="text-emerald-700">
                            <span className="font-bold">NEW: </span>
                            {typeof log.new_value === 'string' ? log.new_value : JSON.stringify(log.new_value)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 font-mono text-slate-500 text-right">
                      {new Date(log.changed_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
