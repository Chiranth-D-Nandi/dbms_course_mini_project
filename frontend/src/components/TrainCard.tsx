// Owner: Person B
'use client';

import Link from 'next/link';
import { TrainSearchResult } from '@/lib/types';
import { ArrowRight, Clock, Train as TrainIcon, Calendar, Zap, AlertCircle } from 'lucide-react';

interface Props {
  train: TrainSearchResult;
  sourceStationId: number;
  destStationId: number;
}

export default function TrainCard({ train, sourceStationId, destStationId }: Props) {
  // Format Train Type Badge
  const getTrainTypeBadge = (type: string) => {
    const t = type.toUpperCase();
    if (t.includes('RAJDHANI')) {
      return 'bg-rose-900 text-white border-rose-800';
    }
    if (t.includes('SHATABDI')) {
      return 'bg-amber-500 text-slate-950 border-amber-600 font-black';
    }
    if (t.includes('SUPERFAST')) {
      return 'bg-blue-700 text-white border-blue-800';
    }
    return 'bg-emerald-700 text-white border-emerald-800';
  };

  // Helper to compute travel duration from "HH:MM:SS" strings
  const getDurationString = (dep: string, arr: string) => {
    try {
      const [dh, dm] = dep.split(':').map(Number);
      const [ah, am] = arr.split(':').map(Number);
      let diffMins = ah * 60 + am - (dh * 60 + dm);
      if (diffMins < 0) diffMins += 24 * 60; // Next-day arrival
      const h = Math.floor(diffMins / 60);
      const m = diffMins % 60;
      return `${h}h ${m > 0 ? `${m}m` : '00m'}`;
    } catch {
      return 'Direct';
    }
  };

  const duration = getDurationString(train.source_departure, train.dest_arrival);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow p-5 space-y-4">
      {/* Train Info Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 border-b border-slate-100 pb-3">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-slate-100 text-[#0f2e5a] rounded-lg mt-0.5">
            <TrainIcon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-extrabold text-base sm:text-lg text-slate-900">
                {train.train_name}
              </h3>
              <span className="font-mono text-xs font-bold bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-300">
                #{train.train_number}
              </span>
              <span
                className={`text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded border ${getTrainTypeBadge(
                  train.train_type
                )}`}
              >
                {train.train_type}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
              <span>Runs: <strong className="text-emerald-700 font-bold">Scheduled for this journey date</strong></span>
              <span>&bull;</span>
              <span>Journey: <strong className="text-slate-700 font-semibold">{train.journey_date}</strong></span>
            </div>
          </div>
        </div>

        <Link
          href={`/trains/${train.train_id}`}
          className="text-xs font-bold text-blue-700 hover:text-blue-900 hover:underline flex items-center gap-1 self-start sm:self-auto"
        >
          <span>View Halt Schedule</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Route & Timetable Schedule Bar */}
      <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 flex items-center justify-between">
        {/* Departure */}
        <div className="text-left">
          <span className="block font-black text-lg sm:text-xl text-slate-900 tracking-tight font-mono">
            {train.source_departure ? train.source_departure.substring(0, 5) : '--:--'}
          </span>
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Departure</span>
        </div>

        {/* Travel Timeline Graphic */}
        <div className="flex flex-col items-center px-4">
          <span className="text-xs font-bold text-slate-700">{duration}</span>
          <div className="w-28 sm:w-44 h-0.5 bg-slate-300 relative my-1.5">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-emerald-600 rounded-full" />
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-[#0f2e5a] rounded-full" />
          </div>
          <span className="text-[10px] font-semibold text-slate-400">
            {train.distance_km} km direct route
          </span>
        </div>

        {/* Arrival */}
        <div className="text-right">
          <span className="block font-black text-lg sm:text-xl text-slate-900 tracking-tight font-mono">
            {train.dest_arrival ? train.dest_arrival.substring(0, 5) : '--:--'}
          </span>
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Arrival</span>
        </div>
      </div>

      {/* Class Availabilities Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-1">
        {train.availability.map((cls) => {
          const isGeneralAvailable = cls.general_available > 0;
          const isTatkalAvailable = cls.tatkal_available > 0;

          return (
            <div
              key={cls.class_code}
              className="border border-slate-200 rounded-xl p-3.5 hover:border-slate-300 transition flex flex-col justify-between bg-white shadow-xs"
            >
              <div>
                {/* Class Code & Base Fare */}
                <div className="flex justify-between items-center mb-1">
                  <span className="font-black text-base text-slate-900">{cls.class_code}</span>
                  <span className="font-mono font-bold text-sm text-slate-800">₹{cls.base_fare}</span>
                </div>
                <div className="text-[11px] font-medium text-slate-500 mb-2 truncate">
                  {cls.class_name}
                </div>

                {/* Quota Availability Status */}
                <div className="space-y-1.5 text-xs bg-slate-50 p-2 rounded-lg border border-slate-100">
                  <div className="flex justify-between items-center">
                    <span className="text-[11px] font-semibold text-slate-500">GENERAL:</span>
                    <span
                      className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${
                        cls.general_available > 5
                          ? 'bg-emerald-100 text-emerald-800'
                          : cls.general_available > 0
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {cls.general_available > 0 ? `AVL ${cls.general_available}` : 'WL / REG'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-[11px] font-bold text-red-600 flex items-center gap-1">
                      <Zap className="w-3 h-3" /> TATKAL:
                    </span>
                    <span
                      className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${
                        cls.tatkal_available > 0
                          ? 'bg-red-100 text-red-800'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {cls.tatkal_available > 0 ? `AVL ${cls.tatkal_available}` : 'CLOSED'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-3 pt-2 border-t border-slate-100 flex flex-col gap-1.5">
                <Link
                  href={`/book/${train.run_id}?class=${cls.class_code}&type=GENERAL&src=${sourceStationId}&dst=${destStationId}`}
                  className="w-full text-center py-1.5 px-2 bg-[#0f2e5a] hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition shadow-xs"
                >
                  Book General
                </Link>
                <Link
                  href={`/book/${train.run_id}?class=${cls.class_code}&type=TATKAL&src=${sourceStationId}&dst=${destStationId}`}
                  className="w-full text-center py-1.5 px-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white rounded-lg text-xs font-black transition shadow-xs flex items-center justify-center gap-1"
                >
                  <Zap className="w-3 h-3" />
                  <span>Book Tatkal (₹{cls.tatkal_fare})</span>
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
