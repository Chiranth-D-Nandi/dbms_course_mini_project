// Owner: Person B
'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TrainSearchResult, Station } from '@/lib/types';
import TrainCard from '@/components/TrainCard';
import StationAutocomplete from '@/components/StationAutocomplete';
import {
  Search,
  Filter,
  ArrowUpDown,
  AlertCircle,
  ArrowLeftRight,
  Train,
  Calendar,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromParam = searchParams.get('from');
  const toParam = searchParams.get('to');
  const dateParam = searchParams.get('date');

  const [fromStation, setFromStation] = useState<Station | null>(null);
  const [toStation, setToStation] = useState<Station | null>(null);
  const [date, setDate] = useState(dateParam || new Date().toISOString().split('T')[0]);

  const [trains, setTrains] = useState<TrainSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Sorting
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'departure' | 'fare' | 'duration'>('departure');

  const executeSearch = async (fromId: number, toId: number, journeyDate: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchTrains(fromId, toId, journeyDate);
      const cls = searchParams.get('class');
      setTrains(cls && cls !== 'ALL' ? data.map(t => ({...t, availability: t.availability.filter(a => a.class_code === cls)})).filter(t => t.availability.length) : data);
    } catch (err: any) {
      setError(err?.error?.message || 'Failed to search trains for the specified route.');
      setTrains([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (fromParam && toParam && dateParam) {
      executeSearch(Number(fromParam), Number(toParam), dateParam);
    }
  }, [fromParam, toParam, dateParam]);

  // Station Swap
  const handleSwapStations = () => {
    const temp = fromStation;
    setFromStation(toStation);
    setToStation(temp);
  };

  // Adjust Date by +/- 1 Day
  const adjustDate = (deltaDays: number) => {
    const current = new Date(date);
    current.setDate(current.getDate() + deltaDays);
    const newDateStr = current.toISOString().split('T')[0];
    setDate(newDateStr);
    if (fromStation && toStation) {
      router.push(`/search?from=${fromStation.station_id}&to=${toStation.station_id}&date=${newDateStr}`);
    } else if (fromParam && toParam) {
      router.push(`/search?from=${fromParam}&to=${toParam}&date=${newDateStr}`);
    }
  };

  const filteredTrains = trains
    .filter((t) => (selectedType === 'ALL' ? true : t.train_type === selectedType))
    .sort((a, b) => {
      if (sortBy === 'departure') {
        return a.source_departure.localeCompare(b.source_departure);
      }
      if (sortBy === 'fare') return Math.min(...a.availability.map(c => c.base_fare)) - Math.min(...b.availability.map(c => c.base_fare));
      return a.distance_km - b.distance_km;
    });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Search Header / Refinement */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (fromStation && toStation) {
              router.push(`/search?from=${fromStation.station_id}&to=${toStation.station_id}&date=${date}`);
            } else if (fromParam && toParam) {
              executeSearch(Number(fromParam), Number(toParam), date);
            }
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr,180px,auto] gap-3 items-end">
            <StationAutocomplete
              label="From Station"
              placeholder="Search origin..."
              selectedStation={fromStation}
              onSelect={setFromStation}
            />

            {/* Swap Button */}
            <div className="flex justify-center md:pb-1">
              <button
                type="button"
                onClick={handleSwapStations}
                title="Swap stations"
                className="p-2.5 rounded-full bg-slate-100 hover:bg-amber-100 hover:text-amber-800 text-slate-600 border border-slate-300 transition"
              >
                <ArrowLeftRight className="w-4 h-4" />
              </button>
            </div>

            <StationAutocomplete
              label="To Station"
              placeholder="Search destination..."
              selectedStation={toStation}
              onSelect={setToStation}
            />

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Journey Date
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs sm:text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#0f2e5a]"
                />
              </div>
            </div>

            <button
              type="submit"
              className="py-2.5 px-6 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black rounded-xl text-sm transition shadow flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4 stroke-[2.5]" />
              <span>Modify Search</span>
            </button>
          </div>
        </form>

        {/* Date Stepper Bar */}
        <div className="flex items-center justify-between border-t border-slate-100 mt-4 pt-3 text-xs">
          <button
            type="button"
            onClick={() => adjustDate(-1)}
            className="flex items-center gap-1 font-semibold text-blue-700 hover:text-blue-900 px-2 py-1 rounded hover:bg-blue-50 transition"
          >
            <ChevronLeft className="w-4 h-4" /> Previous Day
          </button>

          <span className="font-bold text-slate-800">
            Journey Date: <strong className="font-mono text-sm">{date}</strong>
          </span>

          <button
            type="button"
            onClick={() => adjustDate(1)}
            className="flex items-center gap-1 font-semibold text-blue-700 hover:text-blue-900 px-2 py-1 rounded hover:bg-blue-50 transition"
          >
            Next Day <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter and Sort Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-100/80 p-3 rounded-xl border border-slate-200 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-bold text-slate-700">Train Type:</span>
          {['ALL', 'SUPERFAST', 'EXPRESS', 'MAIL', 'RAJDHANI', 'SHATABDI'].map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                selectedType === type
                  ? 'bg-[#0f2e5a] text-white shadow-xs'
                  : 'bg-white text-slate-700 hover:bg-slate-200 border border-slate-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-bold text-slate-700">Sort By:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-semibold focus:outline-none"
          >
            <option value="departure">Departure Time (Earliest First)</option>
            <option value="duration">Route Distance</option>
          </select>
        </div>
      </div>

      {/* Results Section */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-6 animate-pulse space-y-4 shadow-xs">
              <div className="h-5 bg-slate-200 rounded w-1/3" />
              <div className="h-10 bg-slate-100 rounded" />
              <div className="grid grid-cols-4 gap-3">
                {[1, 2, 3, 4].map((j) => (
                  <div key={j} className="h-24 bg-slate-100 rounded-lg" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-10 text-center space-y-2 shadow-xs">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="font-black text-base text-red-800">No Scheduled Trains Found</h3>
          <p className="text-xs text-red-600 max-w-md mx-auto">{error}</p>
        </div>
      ) : filteredTrains.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3 shadow-xs">
          <Search className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="font-black text-slate-800 text-lg">No Trains Found on Selected Date</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Please select alternate dates using the Previous/Next Day buttons or search major interchange stations like SBC (Bengaluru) or MAS (Chennai).
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex justify-between items-center text-xs font-bold text-slate-600 px-1">
            <span>
              Showing {filteredTrains.length} Active Express &amp; Superfast Trains
            </span>
            <span className="text-emerald-700">All Schedules Synchronized</span>
          </div>

          {filteredTrains.map((train) => (
            <TrainCard
              key={train.run_id}
              train={train}
              sourceStationId={Number(fromParam) || 1}
              destStationId={Number(toParam) || 2}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-slate-500">
          <span className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin inline-block mb-2" />
          <p>Loading train search results...</p>
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
