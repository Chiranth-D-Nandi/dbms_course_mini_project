// Owner: Person B
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { BookingDetail } from '@/lib/types';
import { Ticket, ArrowRight, Clock, AlertCircle, Train, CheckCircle2 } from 'lucide-react';

export default function MyBookingsPage() {
  const [bookings, setBookings] = useState<BookingDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMyBookings()
      .then(setBookings)
      .catch((err) => setError(err?.error?.message || 'Failed to load bookings.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-600 uppercase tracking-wider">
            <Ticket className="w-4 h-4" /> Indian Railways E-Tickets
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900">My Ticket Bookings</h1>
          <p className="text-xs text-slate-500 mt-1">
            Summary of confirmed reservations, active seat holds, and cancellations
          </p>
        </div>
        <Link
          href="/search"
          className="self-start sm:self-auto py-2 px-4 bg-[#0f2e5a] hover:bg-slate-800 text-white font-bold rounded-xl text-xs transition shadow-xs flex items-center gap-1.5"
        >
          <Train className="w-4 h-4" />
          <span>Book New Journey</span>
        </Link>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse space-y-3 shadow-xs">
              <div className="h-4 bg-slate-200 rounded w-1/4" />
              <div className="h-6 bg-slate-100 rounded w-3/4" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center text-red-700 text-sm shadow-xs">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="font-semibold">{error}</p>
        </div>
      ) : bookings.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-4 shadow-xs">
          <div className="p-4 bg-slate-100 rounded-full w-fit mx-auto text-slate-400">
            <Ticket className="w-10 h-10" />
          </div>
          <div>
            <h3 className="font-black text-slate-800 text-lg">No Reservation Records Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              You haven't reserved any train journeys yet. Search for trains and book confirmed tickets.
            </p>
          </div>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-black rounded-xl transition shadow"
          >
            <span>Search &amp; Book Trains</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {bookings.map((b) => {
            const isConfirmed = b.status === 'CONFIRMED';
            const isPending = b.status === 'PENDING';
            const isCancelled = b.status === 'CANCELLED';

            return (
              <div
                key={b.pnr}
                className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-slate-300 transition shadow-xs hover:shadow-md flex flex-col sm:flex-row justify-between sm:items-center gap-4"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <span className="font-mono font-black text-base text-slate-900">PNR #{b.pnr}</span>
                    <span
                      className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${
                        isConfirmed
                          ? 'bg-emerald-100 text-emerald-800'
                          : isPending
                          ? 'bg-amber-100 text-amber-800 animate-pulse'
                          : isCancelled
                          ? 'bg-red-100 text-red-800'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {b.status}
                    </span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded uppercase">
                      {b.booking_type}
                    </span>
                  </div>

                  <div className="text-xs space-y-0.5">
                    <p className="font-bold text-slate-900">
                      {b.train_name} <span className="font-mono text-blue-700">(#{b.train_number})</span> &bull; Class {b.class_code}
                    </p>
                    <p className="text-slate-500">
                      {b.source_station} &rarr; {b.dest_station} &bull; Journey Date: <strong>{b.journey_date}</strong>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100 justify-between sm:justify-end">
                  <div className="text-left sm:text-right">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Fare</span>
                    <span className="font-mono font-black text-base text-slate-900">₹{b.total_fare}</span>
                  </div>

                  <div className="flex gap-2">
                    {isPending && (
                      <Link
                        href={`/pay/${b.pnr}`}
                        className="py-2 px-3.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-black rounded-xl text-xs transition shadow-xs flex items-center gap-1"
                      >
                        <Clock className="w-3.5 h-3.5" />
                        <span>Pay Now</span>
                      </Link>
                    )}
                    <Link
                      href={`/bookings/${b.pnr}`}
                      className="py-2 px-3.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl text-xs transition flex items-center gap-1.5"
                    >
                      <span>View Slip</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
