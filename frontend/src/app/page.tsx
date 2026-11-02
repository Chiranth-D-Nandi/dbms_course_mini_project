// Owner: Person B
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import StationAutocomplete from '@/components/StationAutocomplete';
import { Station, BookingDetail } from '@/lib/types';
import { api } from '@/lib/api';
import {
  Calendar,
  Search,
  Sparkles,
  Zap,
  ShieldCheck,
  Clock,
  ArrowRight,
  ArrowLeftRight,
  Ticket,
  AlertTriangle,
  CheckCircle2,
  Train,
  MapPin,
  Flame,
  Award,
  RefreshCw,
} from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  // Tab State: 'BOOK' | 'PNR' | 'SCHEDULE'
  const [activeTab, setActiveTab] = useState<'BOOK' | 'PNR' | 'SCHEDULE'>('BOOK');

  // Search Form State
  const [sourceStation, setSourceStation] = useState<Station | null>(null);
  const [destStation, setDestStation] = useState<Station | null>(null);
  const [quota, setQuota] = useState<'GENERAL' | 'TATKAL' | 'LADIES' | 'SENIOR_CITIZEN'>('GENERAL');
  const [classCode, setClassCode] = useState<string>('ALL');
  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  });

  // PNR Search State
  const [pnrInput, setPnrInput] = useState('');
  const [pnrLoading, setPnrLoading] = useState(false);
  const [pnrResult, setPnrResult] = useState<BookingDetail | null>(null);
  const [pnrError, setPnrError] = useState<string | null>(null);

  // Train Schedule quick lookup
  const [trainQuery, setTrainQuery] = useState('');

  // Semantic search state
  const [semanticQuery, setSemanticQuery] = useState('');
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [semanticResults, setSemanticResults] = useState<any[]>([]);

  // Swap From & To Stations
  const handleSwapStations = () => {
    const temp = sourceStation;
    setSourceStation(destStation);
    setDestStation(temp);
  };

  // Date Quick Chips
  const setQuickDate = (offsetDays: number) => {
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    setDate(d.toISOString().split('T')[0]);
  };

  const handleStandardSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceStation || !destStation) {
      alert('Please select both Origin (From) and Destination (To) stations.');
      return;
    }
    if (sourceStation.station_id === destStation.station_id) {
      alert('Origin and Destination stations cannot be identical.');
      return;
    }
    router.push(
      `/search?from=${sourceStation.station_id}&to=${destStation.station_id}&date=${date}&quota=${quota}&class=${classCode}`
    );
  };

  const handlePnrLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pnrInput.trim()) return;
    setPnrLoading(true);
    setPnrError(null);
    setPnrResult(null);

    try {
      const res = await api.getBooking(Number(pnrInput.trim()));
      setPnrResult(res);
    } catch (err: any) {
      setPnrError(err?.error?.message || 'PNR record not found or invalid format.');
    } finally {
      setPnrLoading(false);
    }
  };

  const handleSemanticSearch = async (e: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const queryToUse = customQuery || semanticQuery;
    if (!queryToUse.trim()) return;
    setSemanticLoading(true);
    try {
      const data = await api.searchTrainsSemantic(queryToUse);
      setSemanticResults(data);
    } catch {
      setSemanticResults([]);
    } finally {
      setSemanticLoading(false);
    }
  };

  // Quick route picker
  const handleSelectQuickRoute = (srcId: number, dstId: number) => {
    router.push(`/search?from=${srcId}&to=${dstId}&date=${date}`);
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Official Railway Notice Ticker */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-900 font-medium">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 overflow-hidden">
            <span className="flex items-center gap-1 bg-amber-500 text-slate-900 text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-wider shrink-0">
              <Zap className="w-3 h-3" /> Tatkal Advisory
            </span>
            <p className="truncate text-xs text-amber-950 font-semibold">
              Tatkal window for AC Classes (1A, 2A, 3A, CC) opens at 10:00 AM daily • Non-AC (SL) opens at 11:00 AM • Seats held for 5 minutes during payment • Carry original Govt Photo ID.
            </p>
          </div>
          <a
            href="/help"
            className="text-[11px] font-bold text-amber-800 hover:text-amber-950 underline shrink-0 hidden sm:inline"
          >
            Tatkal Guidelines &rarr;
          </a>
        </div>
      </div>

      {/* Hero Section with Unified Reservation Hub */}
      <section className="relative bg-gradient-to-br from-[#0a1f3d] via-[#0f2e5a] to-[#1a365d] text-white pt-10 pb-16 px-4 sm:px-6 lg:px-8 shadow-inner overflow-hidden">
        {/* Subtle decorative background gradient circles */}
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -mb-12 -ml-12 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-5xl mx-auto space-y-6 relative z-10">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 bg-amber-400/15 border border-amber-400/30 text-amber-300 px-3.5 py-1 rounded-full text-xs font-bold tracking-wide uppercase">
              <Flame className="w-3.5 h-3.5 text-amber-400" />
              National Passenger Reservation System
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-white">
              Book Train Tickets &amp; Tatkal
            </h1>
            <p className="max-w-2xl mx-auto text-slate-300 text-xs sm:text-sm">
              Official high-speed reservation engine with guaranteed single-seat allocation, 5-minute checkout hold, and instant cancellation refunds.
            </p>
          </div>

          {/* Tabbed Interactive Hub */}
          <div className="bg-white text-slate-900 rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            {/* Tab Headers */}
            <div className="flex border-b border-slate-200 bg-slate-50/80 text-xs sm:text-sm font-bold">
              <button
                type="button"
                onClick={() => setActiveTab('BOOK')}
                className={`flex-1 py-3.5 px-4 text-center transition flex items-center justify-center gap-2 ${
                  activeTab === 'BOOK'
                    ? 'bg-white text-[#0f2e5a] border-b-2 border-[#0f2e5a] shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Train className="w-4 h-4 text-amber-500" />
                <span>Book Train Tickets</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('PNR')}
                className={`flex-1 py-3.5 px-4 text-center transition flex items-center justify-center gap-2 ${
                  activeTab === 'PNR'
                    ? 'bg-white text-[#0f2e5a] border-b-2 border-[#0f2e5a] shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Ticket className="w-4 h-4 text-blue-600" />
                <span>Check PNR Status</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('SCHEDULE')}
                className={`flex-1 py-3.5 px-4 text-center transition flex items-center justify-center gap-2 ${
                  activeTab === 'SCHEDULE'
                    ? 'bg-white text-[#0f2e5a] border-b-2 border-[#0f2e5a] shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Clock className="w-4 h-4 text-emerald-600" />
                <span>Train Timetable</span>
              </button>
            </div>

            {/* Tab 1: Book Train Tickets */}
            {activeTab === 'BOOK' && (
              <div className="p-6 space-y-5">
                <form onSubmit={handleStandardSearch} className="space-y-4">
                  {/* Stations Row with Swap Button */}
                  <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr] gap-3 items-end">
                    <StationAutocomplete
                      label="From (Origin Station)"
                      placeholder="e.g. SBC, Bengaluru City"
                      selectedStation={sourceStation}
                      onSelect={setSourceStation}
                    />

                    {/* Swap Station Button */}
                    <div className="flex justify-center md:pb-1">
                      <button
                        type="button"
                        onClick={handleSwapStations}
                        title="Swap Origin and Destination"
                        className="p-2.5 rounded-full bg-slate-100 hover:bg-amber-100 hover:text-amber-700 text-slate-600 border border-slate-300 transition shadow-xs group"
                      >
                        <ArrowLeftRight className="w-4 h-4 transition group-hover:rotate-180" />
                      </button>
                    </div>

                    <StationAutocomplete
                      label="To (Destination Station)"
                      placeholder="e.g. MAS, Chennai Central"
                      selectedStation={destStation}
                      onSelect={setDestStation}
                    />
                  </div>

                  {/* Date, Quota, Class Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                    {/* Journey Date */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Journey Date
                        </label>
                        <div className="flex gap-1">
                          <button
                            type="button"
                            onClick={() => setQuickDate(0)}
                            className="text-[10px] font-semibold text-blue-600 hover:underline px-1"
                          >
                            Today
                          </button>
                          <span className="text-slate-300 text-[10px]">|</span>
                          <button
                            type="button"
                            onClick={() => setQuickDate(1)}
                            className="text-[10px] font-semibold text-blue-600 hover:underline px-1"
                          >
                            Tomorrow
                          </button>
                          <span className="text-slate-300 text-[10px]">|</span>
                          <button
                            type="button"
                            onClick={() => setQuickDate(2)}
                            className="text-[10px] font-semibold text-blue-600 hover:underline px-1"
                          >
                            +2d
                          </button>
                        </div>
                      </div>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                        <input
                          type="date"
                          required
                          value={date}
                          onChange={(e) => setDate(e.target.value)}
                          className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs sm:text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#0f2e5a]"
                        />
                      </div>
                    </div>

                    {/* Quota Selector */}
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                        Quota
                      </label>
                      <select
                        value={quota}
                        onChange={(e) => setQuota(e.target.value as any)}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs sm:text-sm font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-[#0f2e5a]"
                      >
                        <option value="GENERAL">GENERAL QUOTA</option>
                        <option value="TATKAL">TATKAL QUOTA (Opens 10 AM)</option>
                        <option value="LADIES">LADIES QUOTA</option>
                        <option value="SENIOR_CITIZEN">LOWER BERTH / SR CITIZEN</option>
                      </select>
                    </div>

                    {/* Class Selector */}
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                        Travel Class
                      </label>
                      <select
                        value={classCode}
                        onChange={(e) => setClassCode(e.target.value)}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs sm:text-sm font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-[#0f2e5a]"
                      >
                        <option value="ALL">All Classes</option>
                        <option value="1A">AC 1st Class (1A)</option>
                        <option value="2A">AC 2 Tier (2A)</option>
                        <option value="3A">AC 3 Tier (3A)</option>
                        <option value="SL">Sleeper (SL)</option>
                        <option value="CC">AC Chair Car (CC)</option>
                      </select>
                    </div>
                  </div>

                  {/* Submit CTA Button */}
                  <div className="pt-2">
                    <button
                      type="submit"
                      className="w-full py-3 px-6 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-sm sm:text-base rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                    >
                      <Search className="w-5 h-5 stroke-[2.5]" />
                      <span>Search Trains &amp; Seat Availability</span>
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Tab 2: PNR Status Lookup */}
            {activeTab === 'PNR' && (
              <div className="p-6 space-y-4">
                <p className="text-xs text-slate-600">
                  Enter your 8-digit or 10-digit Passenger Name Record (PNR) number to inspect live booking confirmation, coach assignment, and seat berth numbers.
                </p>

                <form onSubmit={handlePnrLookup} className="flex flex-col sm:flex-row gap-3">
                  <div className="relative flex-1">
                    <Ticket className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                    <input
                      type="text"
                      required
                      value={pnrInput}
                      onChange={(e) => setPnrInput(e.target.value)}
                      placeholder="Enter 8-digit PNR Number (e.g. 10000001)"
                      className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#0f2e5a]"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={pnrLoading}
                    className="py-2.5 px-6 bg-[#0f2e5a] hover:bg-blue-900 text-white font-bold text-sm rounded-lg transition shadow flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {pnrLoading ? (
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <Search className="w-4 h-4" />
                        <span>Get PNR Status</span>
                      </>
                    )}
                  </button>
                </form>

                {/* PNR Error */}
                {pnrError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                    <span>{pnrError}</span>
                  </div>
                )}

                {/* PNR Result Preview Card */}
                {pnrResult && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
                    <div className="flex flex-wrap justify-between items-center gap-2 border-b border-slate-200 pb-2">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500 block">PNR NUMBER</span>
                        <span className="font-mono font-black text-lg text-[#0f2e5a]">#{pnrResult.pnr}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded uppercase ${
                            pnrResult.status === 'CONFIRMED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : pnrResult.status === 'PENDING'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {pnrResult.status}
                        </span>
                        <button
                          onClick={() => router.push(`/bookings/${pnrResult.pnr}`)}
                          className="text-xs font-bold text-blue-700 hover:underline flex items-center gap-1"
                        >
                          View E-Ticket Slip &rarr;
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase">Train</span>
                        <span className="font-bold text-slate-800">{pnrResult.train_name} ({pnrResult.train_number})</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase">Journey Date</span>
                        <span className="font-bold text-slate-800">{pnrResult.journey_date}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase">Route</span>
                        <span className="font-bold text-slate-800">{pnrResult.source_station} &rarr; {pnrResult.dest_station}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase">Class &amp; Quota</span>
                        <span className="font-bold text-slate-800">{pnrResult.class_code} &bull; {pnrResult.booking_type}</span>
                      </div>
                    </div>

                    {/* Passenger List */}
                    <div className="pt-2 border-t border-slate-200">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                        Allocated Berths ({pnrResult.passengers?.length || 0} Passengers)
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {pnrResult.passengers?.map((p, idx) => (
                          <div
                            key={idx}
                            className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-xs flex items-center gap-2"
                          >
                            <span className="font-semibold text-slate-700">{p.name}</span>
                            <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded text-[11px]">
                              {p.coach_number ? `${p.coach_number}-${p.seat_number} (${p.berth_type})` : 'Pending'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Train Timetable Lookup */}
            {activeTab === 'SCHEDULE' && (
              <div className="p-6 space-y-4">
                <p className="text-xs text-slate-600">
                  Search scheduled passenger, superfast, and Rajdhani express trains to view station halts, arrival/departure schedules, and platform info.
                </p>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Train className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                    <input
                      type="text"
                      value={trainQuery}
                      onChange={(e) => setTrainQuery(e.target.value)}
                      placeholder="Enter Train Number (e.g. 12639, 12951, 12007) or Name"
                      className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#0f2e5a]"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      if (trainQuery.includes('12639')) router.push('/trains/1');
                      else if (trainQuery.includes('12007')) router.push('/trains/2');
                      else router.push('/search');
                    }}
                    className="py-2.5 px-6 bg-[#0f2e5a] hover:bg-blue-900 text-white font-bold text-sm rounded-lg transition shadow"
                  >
                    View Timetable
                  </button>
                </div>

                <div className="flex flex-wrap gap-2 text-xs pt-1">
                  <span className="text-slate-500 font-medium">Quick Links:</span>
                  <button
                    onClick={() => router.push('/trains/1')}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 px-2 py-0.5 rounded font-mono font-semibold"
                  >
                    #12639 Brindavan Express
                  </button>
                  <button
                    onClick={() => router.push('/trains/2')}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 px-2 py-0.5 rounded font-mono font-semibold"
                  >
                    #12007 Shatabdi Express
                  </button>
                  <button
                    onClick={() => router.push('/trains/3')}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 px-2 py-0.5 rounded font-mono font-semibold"
                  >
                    #12951 Mumbai Rajdhani
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Popular Travel Routes Carousel / Grid */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex justify-between items-end mb-4">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-600 uppercase tracking-wider">
              <Award className="w-4 h-4" /> Recommended High-Speed Routes
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900">Popular Train Corridors</h2>
          </div>
          <span className="text-xs text-slate-500 hidden sm:inline">Direct 1-Click Search</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Corridor 1: SBC to MAS */}
          <div
            onClick={() => handleSelectQuickRoute(1, 2)}
            className="group cursor-pointer bg-white border border-slate-200 hover:border-amber-400 rounded-xl p-4 shadow-xs hover:shadow-md transition flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                  Superfast &bull; ~362 km
                </span>
                <span className="text-xs font-bold text-slate-400 group-hover:text-amber-500 transition">
                  5h 30m
                </span>
              </div>
              <h3 className="font-extrabold text-base text-slate-900 group-hover:text-blue-700 transition">
                Bengaluru &rarr; Chennai
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                SBC (KSR) to MAS (Central) &bull; Shatabdi &amp; Brindavan Exp
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-blue-600">
              <span>View Available Trains</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </div>

          {/* Corridor 2: NDLS to BCT */}
          <div
            onClick={() => handleSelectQuickRoute(3, 4)}
            className="group cursor-pointer bg-white border border-slate-200 hover:border-amber-400 rounded-xl p-4 shadow-xs hover:shadow-md transition flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-bold bg-red-50 text-red-700 px-2 py-0.5 rounded">
                  Rajdhani &bull; ~1384 km
                </span>
                <span className="text-xs font-bold text-slate-400 group-hover:text-amber-500 transition">
                  15h 30m
                </span>
              </div>
              <h3 className="font-extrabold text-base text-slate-900 group-hover:text-blue-700 transition">
                New Delhi &rarr; Mumbai
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                NDLS to BCT (Central) &bull; Mumbai Rajdhani &amp; August Kranti
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-blue-600">
              <span>View Available Trains</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </div>

          {/* Corridor 3: NDLS to HWH */}
          <div
            onClick={() => handleSelectQuickRoute(3, 5)}
            className="group cursor-pointer bg-white border border-slate-200 hover:border-amber-400 rounded-xl p-4 shadow-xs hover:shadow-md transition flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-bold bg-purple-50 text-purple-700 px-2 py-0.5 rounded">
                  Rajdhani &bull; ~1450 km
                </span>
                <span className="text-xs font-bold text-slate-400 group-hover:text-amber-500 transition">
                  17h 00m
                </span>
              </div>
              <h3 className="font-extrabold text-base text-slate-900 group-hover:text-blue-700 transition">
                New Delhi &rarr; Howrah
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                NDLS to HWH (Kolkata) &bull; Howrah Rajdhani &amp; Poorva Exp
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-blue-600">
              <span>View Available Trains</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </div>

          {/* Corridor 4: SBC to HYB */}
          <div
            onClick={() => handleSelectQuickRoute(1, 6)}
            className="group cursor-pointer bg-white border border-slate-200 hover:border-amber-400 rounded-xl p-4 shadow-xs hover:shadow-md transition flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded">
                  Express &bull; ~610 km
                </span>
                <span className="text-xs font-bold text-slate-400 group-hover:text-amber-500 transition">
                  11h 15m
                </span>
              </div>
              <h3 className="font-extrabold text-base text-slate-900 group-hover:text-blue-700 transition">
                Bengaluru &rarr; Hyderabad
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                SBC to HYB (Kacheguda) &bull; Kacheguda Express
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-blue-600">
              <span>View Available Trains</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </div>
        </div>
      </section>

      {/* Smart Natural Language Journey Finder (ChromaDB Vector Copilot) */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-xl border border-indigo-900/50 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-indigo-500/20 border border-indigo-400/30 rounded-lg text-indigo-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-black text-white">
                  IRCTC Smart Travel Copilot
                </h2>
                <p className="text-xs text-indigo-200">
                  Describe your ideal train trip in natural language (offline vector retrieval via ChromaDB)
                </p>
              </div>
            </div>
            <span className="text-[11px] font-mono text-indigo-300 bg-indigo-900/60 border border-indigo-700/50 px-2.5 py-1 rounded-full self-start sm:self-auto">
              Embeddings: all-MiniLM-L6-v2
            </span>
          </div>

          {/* Quick Prompt Chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px] font-semibold">Try queries:</span>
            {[
              'Fast morning superfast from Bangalore to Chennai',
              'Overnight train with AC coaches to Delhi',
              'Comfortable Rajdhani express with pantry meals',
              'Budget sleeper train to Hyderabad',
            ].map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={(e) => {
                  setSemanticQuery(chip);
                  handleSemanticSearch(e, chip);
                }}
                className="bg-white/10 hover:bg-white/20 text-indigo-200 hover:text-white px-2.5 py-1 rounded-md text-[11px] transition border border-white/10"
              >
                &ldquo;{chip}&rdquo;
              </button>
            ))}
          </div>

          <form onSubmit={handleSemanticSearch} className="flex flex-col sm:flex-row gap-2 pt-1">
            <input
              type="text"
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              placeholder="e.g. Fast overnight superfast express with AC 3-tier berths from Bangalore to Chennai"
              className="flex-1 px-4 py-2.5 bg-slate-800 border border-indigo-500/40 rounded-xl text-xs sm:text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <button
              type="submit"
              disabled={semanticLoading}
              className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 text-white font-bold rounded-xl text-xs sm:text-sm transition shadow flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {semanticLoading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Find Best Match</span>
                </>
              )}
            </button>
          </form>

          {/* Results grid */}
          {semanticResults.length > 0 && (
            <div className="pt-3 border-t border-indigo-900/50 space-y-2">
              <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider block">
                Top Semantic Matches:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {semanticResults.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => router.push(`/trains/${item.train_id}`)}
                    className="cursor-pointer bg-slate-800/90 border border-indigo-500/30 hover:border-indigo-400 p-4 rounded-xl transition shadow flex justify-between items-center group"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white group-hover:text-amber-400 transition">
                          {item.train_name}
                        </span>
                        <span className="text-[10px] font-mono bg-indigo-900 text-indigo-200 px-1.5 py-0.5 rounded">
                          #{item.train_number}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1 line-clamp-1">{item.description}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-indigo-400 group-hover:translate-x-1 transition shrink-0 ml-3" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Trust & Railway Engineering Highlights */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-2">
            <div className="p-2.5 bg-blue-50 text-blue-700 rounded-lg w-fit">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-extrabold text-sm text-slate-900">Zero Double-Booking</h3>
            <p className="text-xs text-slate-600">
              ACID stored procedures with row-level locks prevent any race condition, guaranteeing 1 passenger per berth.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-2">
            <div className="p-2.5 bg-amber-50 text-amber-700 rounded-lg w-fit">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="font-extrabold text-sm text-slate-900">5-Minute Seat Hold</h3>
            <p className="text-xs text-slate-600">
              Your selected berth is exclusively reserved for 300 seconds while you complete payment simulation.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-2">
            <div className="p-2.5 bg-emerald-50 text-emerald-700 rounded-lg w-fit">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="font-extrabold text-sm text-slate-900">Instant UPI Refunds</h3>
            <p className="text-xs text-slate-600">
              Automated cancellation calculations refund up to 90% back to source accounts instantly.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-2">
            <div className="p-2.5 bg-purple-50 text-purple-700 rounded-lg w-fit">
              <Ticket className="w-6 h-6" />
            </div>
            <h3 className="font-extrabold text-sm text-slate-900">Official E-Ticket Slip</h3>
            <p className="text-xs text-slate-600">
              Generate and print authentic Electronic Reservation Slips (ERS) with QR verification.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
