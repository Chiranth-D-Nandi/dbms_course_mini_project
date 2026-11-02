// Owner: Person B
import { TrainStop } from '@/lib/types';
import { MapPin, Clock } from 'lucide-react';

interface Props {
  stops: TrainStop[];
}

export default function RouteTimeline({ stops }: Props) {
  return (
    <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-2.5 sm:before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
      {stops.map((stop, idx) => {
        const isFirst = idx === 0;
        const isLast = idx === stops.length - 1;

        return (
          <div key={stop.stop_seq} className="relative group">
            {/* Dot */}
            <div
              className={`absolute -left-6 sm:-left-8 top-1 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                isFirst || isLast
                  ? 'bg-railway-navy border-railway-gold text-white'
                  : 'bg-white border-slate-400 group-hover:border-railway-blue'
              }`}
            >
              <div
                className={`w-1.5 h-1.5 rounded-full ${
                  isFirst || isLast ? 'bg-railway-gold' : 'bg-slate-400'
                }`}
              />
            </div>

            {/* Content Card */}
            <div className="bg-white border border-slate-200 rounded-lg p-3 hover:border-slate-300 transition shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-slate-900">{stop.station_name}</span>
                  <span className="font-mono text-xs font-semibold bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">
                    {stop.station_code}
                  </span>
                  {stop.day_offset > 0 && (
                    <span className="text-[10px] bg-amber-100 text-amber-800 font-bold px-1.5 py-0.5 rounded">
                      Day +{stop.day_offset}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-3">
                  <span>Stop #{stop.stop_seq}</span>
                  <span>&bull;</span>
                  <span>{stop.distance_km} km from origin</span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-sans">Arrival</span>
                  <span className="font-bold text-slate-800">{stop.arrival_time || 'SOURCE'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-sans">Departure</span>
                  <span className="font-bold text-slate-800">{stop.departure_time || 'DESTINATION'}</span>
                </div>
                {stop.halt_duration_minutes > 0 && (
                  <div className="bg-blue-50 text-blue-800 px-2 py-1 rounded text-[11px] font-sans font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{stop.halt_duration_minutes}m halt</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
