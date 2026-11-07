// Owner: Person B
'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { FaqChunk } from '@/lib/types';
import { HelpCircle, Search, Sparkles, BookOpen, ShieldCheck, Clock, FileText } from 'lucide-react';

export default function HelpPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<FaqChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState('');
  const [category, setCategory] = useState<string>('ALL');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true); setSearched(true); setError('');
    try {
      const data = await api.searchFaq(query, category === 'ALL' ? undefined : category);
      setResults(data);
    } catch (e: any) {
      setError(e?.error?.message || 'Search is unavailable.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const defaultPolicies: FaqChunk[] = [
    {
      chunk_id: 'default-1',
      title: 'Tatkal Booking Window Timings',
      category: 'TATKAL_RULES',
      content: 'Tatkal booking opens at 10:00 AM for AC classes (1A, 2A, 3A, CC) and 11:00 AM for Non-AC classes (SL) on the day prior to train departure from the originating station. A maximum of 4 passengers can be booked per PNR under Tatkal quota.',
    },
    {
      chunk_id: 'default-2',
      title: 'Cancellation and Refund Policy',
      category: 'CANCELLATION',
      content: 'No refund is admissible on cancellation of confirmed Tatkal tickets. For General quota: 90% refund if cancelled > 48 hours prior to scheduled departure, 50% if cancelled between 12 and 48 hours, 25% between 4 and 12 hours, and 0% within 4 hours.',
    },
    {
      chunk_id: 'default-3',
      title: 'Valid Government ID Proofs',
      category: 'ID_PROOF',
      content: 'At least one passenger on a Tatkal booking must carry an original government ID proof during the journey. Acceptable documents: Aadhaar Card, Passport, PAN Card, Voter Identity Card, excluding Driving License in this demo.',
    },
    {
      chunk_id: 'default-4',
      title: '8-Minute Seat Hold & Auto-Release',
      category: 'SEAT_HOLD',
      content: 'When you initiate a reservation, seats are temporarily placed in HELD status for 480 seconds (8 minutes). A recurring background MySQL event (ev_release_expired_holds) sweeps every 30 seconds and releases held seats back to the inventory if payment is not completed.',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex p-3 bg-indigo-50 text-indigo-700 rounded-xl mb-1 shadow-xs border border-indigo-100">
          <BookOpen className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900">Railway Ticketing Policies & FAQ</h1>
        <p className="text-xs text-slate-600 max-w-lg mx-auto">
          Vector semantic knowledge base powered by ChromaDB and sentence-transformers. Search Tatkal rules, cancellation slabs, and ID mandates in natural language.
        </p>
      </div>

      {/* Semantic Search Box */}
      <div className="bg-white border border-indigo-200 rounded-2xl p-6 shadow-sm space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Can I get a refund if I cancel my Tatkal ticket?"
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm transition flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Search Knowledge Base</span>
              </>
            )}
          </button>
        </form>

        {/* Categories */}
        <div className="flex flex-wrap items-center gap-2 text-xs pt-1">
          <span className="font-semibold text-slate-500">Filter Topic:</span>
          {['ALL', 'Tatkal Rules', 'Cancellation & Refunds', 'Travel Policies', 'Booking & PNR', 'Payment & Security'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-2.5 py-1 rounded transition text-xs ${
                category === cat ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {error && <p role="alert" className="text-red-700">{error}</p>}
      {searched && !loading && !error && results.length === 0 && <p>No matching policies found. Try another topic or query.</p>}
      {/* Search Results or Default Policies */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
          {results.length > 0 ? `Semantic Vector Matches (${results.length})` : 'Core Ticketing Guidelines'}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(searched ? results : defaultPolicies).map((item, idx) => (
            <div
              key={idx}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-indigo-300 transition space-y-2 flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start gap-2 mb-1">
                  <h3 className="font-bold text-sm text-slate-900">{item.title}</h3>
                  {item.similarity_score && (
                    <span className="bg-indigo-100 text-indigo-800 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded">
                      {(item.similarity_score * 100).toFixed(0)}% match
                    </span>
                  )}
                </div>
                <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400 block mb-2">
                  {item.category.replace('_', ' ')}
                </span>
                <p className="text-xs text-slate-600 leading-relaxed">{item.content}</p>
              </div>

              <div className="pt-2 text-[10px] text-slate-400 border-t border-slate-100 flex items-center gap-1">
                <FileText className="w-3 h-3" />
                <span>Project demonstration policy — consult official railway guidance for real travel</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
