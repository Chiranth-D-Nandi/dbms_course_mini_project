// Owner: Person B
'use client';

import { useState } from 'react';
import { SeatMapItem } from '@/lib/types';
import { ShieldCheck, Zap, Info } from 'lucide-react';

interface Props {
  seats: SeatMapItem[];
  selectedClass: string;
}

export default function SeatMap({ seats, selectedClass }: Props) {
  const [selectedCoach, setSelectedCoach] = useState<string>('ALL');

  const filteredSeats = seats.filter((s) => {
    if (s.class_code !== selectedClass) return false;
    if (selectedCoach !== 'ALL' && s.coach_number !== selectedCoach) return false;
    return true;
  });

  const coaches = Array.from(
    new Set(seats.filter((s) => s.class_code === selectedClass).map((s) => s.coach_number))
  );

  const getBerthFullName = (code: string) => {
    switch (code) {
      case 'LB':
        return 'Lower Berth';
      case 'MB':
        return 'Middle Berth';
      case 'UB':
        return 'Upper Berth';
      case 'SL':
        return 'Side Lower';
      case 'SU':
        return 'Side Upper';
      case 'WS':
        return 'Window Seat';
      case 'AS':
        return 'Aisle Seat';
      default:
        return code;
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-extrabold text-sm text-slate-900">
            Interactive Coach Layout &amp; Seat Availability
          </h3>
          <p className="text-xs text-slate-500">
            Real-time seat states synchronized directly with railway reservation engine
          </p>
        </div>

        {/* Coach Selector */}
        {coaches.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-500 font-bold">Select Coach:</span>
            <button
              onClick={() => setSelectedCoach('ALL')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition ${
                selectedCoach === 'ALL'
                  ? 'bg-[#0f2e5a] text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              All Coaches
            </button>
            {coaches.map((c) => (
              <button
                key={c}
                onClick={() => setSelectedCoach(c)}
                className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold transition ${
                  selectedCoach === c
                    ? 'bg-[#0f2e5a] text-white shadow-xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Legend & Berth Types Reference */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 bg-emerald-100 border border-emerald-400 rounded-md" />
            <span className="text-slate-700 font-medium">Available (General)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 bg-red-100 border border-red-400 rounded-md" />
            <span className="text-slate-700 font-medium">Available (Tatkal)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 bg-amber-200 border border-amber-400 rounded-md animate-pulse" />
            <span className="text-slate-700 font-medium">Held (5-Min Lock)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 bg-slate-200 border border-slate-300 rounded-md" />
            <span className="text-slate-500 font-medium">Occupied / Booked</span>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 hidden md:block">
          Berth Key: <strong>LB</strong>: Lower &bull; <strong>MB</strong>: Middle &bull; <strong>UB</strong>: Upper &bull; <strong>SL</strong>: Side Lower &bull; <strong>SU</strong>: Side Upper
        </div>
      </div>

      {/* Coach Direction Bar */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 font-bold px-2 py-1 bg-slate-100 rounded-md uppercase tracking-wider">
        <span>&larr; Engine / Vestibule Entry</span>
        <span>Aisle / Corridor</span>
        <span>Emergency Exit / Washrooms &rarr;</span>
      </div>

      {/* Seats Grid */}
      {filteredSeats.length === 0 ? (
        <div className="py-10 text-center text-xs text-slate-400">
          No seat records initialized for class {selectedClass}. Check inventory in admin portal.
        </div>
      ) : (
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2.5 max-h-80 overflow-y-auto custom-scrollbar p-1">
          {filteredSeats.map((seat) => {
            const isAvailable = seat.seat_status === 'AVAILABLE';
            const isHeld = seat.seat_status === 'HELD';
            const isBooked = seat.seat_status === 'BOOKED';
            const isTatkal = seat.quota_type === 'TATKAL';

            let styling = 'bg-slate-100 border-slate-200 text-slate-400 opacity-75';
            if (isAvailable && isTatkal) {
              styling = 'bg-red-50 border-red-300 text-red-900 hover:bg-red-100 hover:border-red-400 shadow-xs';
            } else if (isAvailable && !isTatkal) {
              styling = 'bg-emerald-50 border-emerald-300 text-emerald-900 hover:bg-emerald-100 hover:border-emerald-400 shadow-xs';
            } else if (isHeld) {
              styling = 'bg-amber-100 border-amber-400 text-amber-900 animate-pulse font-bold shadow-xs';
            }

            return (
              <div
                key={seat.seat_id}
                title={`Seat #${seat.seat_number} (${getBerthFullName(seat.berth_type)}) - ${seat.quota_type} Quota`}
                className={`p-2 border rounded-xl text-center flex flex-col justify-between transition cursor-default ${styling}`}
              >
                <div className="flex justify-between items-center text-[10px] font-mono leading-none">
                  <span className="font-bold text-slate-700">{seat.coach_number}</span>
                  <span className="text-[9px] uppercase font-bold tracking-tight px-1 rounded bg-black/5">
                    {seat.berth_type}
                  </span>
                </div>

                <div className="my-1.5 font-black text-sm tracking-tight">
                  #{seat.seat_number}
                </div>

                <div className="text-[8px] uppercase tracking-wider font-extrabold opacity-80 truncate">
                  {isHeld ? '5M HELD' : isBooked ? 'BOOKED' : seat.quota_type}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
