// Owner: Person B
'use client';

import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { Station } from '@/lib/types';
import { MapPin, Search } from 'lucide-react';

interface Props {
  label: string;
  placeholder: string;
  selectedStation: Station | null;
  onSelect: (station: Station) => void;
}

export default function StationAutocomplete({
  label,
  placeholder,
  selectedStation,
  onSelect,
}: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Station[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedStation) {
      setQuery(`${selectedStation.station_name} (${selectedStation.station_code})`);
    }
  }, [selectedStation]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (val.trim().length < 1) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    try {
      const data = await api.searchStations(val);
      setResults(data);
      setIsOpen(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (station: Station) => {
    onSelect(station);
    setQuery(`${station.station_name} (${station.station_code})`);
    setIsOpen(false);
  };

  return (
    <div ref={wrapperRef} className="relative w-full">
      <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
        {label}
      </label>
      <div className="relative">
        <MapPin className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder={placeholder}
          className="w-full pl-9 pr-8 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-railway-blue"
        />
        {loading && (
          <div className="absolute right-3 top-2.5">
            <span className="block w-4 h-4 rounded-full border-2 border-railway-blue border-t-transparent animate-spin" />
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute z-20 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-xl max-h-60 overflow-y-auto">
          {results.map((st) => (
            <button
              key={st.station_id}
              type="button"
              onClick={() => handleSelect(st)}
              className="w-full text-left px-4 py-2 hover:bg-slate-50 border-b border-slate-100 last:border-b-0 text-sm flex items-center justify-between"
            >
              <div>
                <span className="font-semibold text-slate-900">{st.station_name}</span>
                <span className="text-xs text-slate-500 ml-1.5">&bull; {st.city}, {st.state}</span>
              </div>
              <span className="bg-slate-100 text-slate-700 font-mono text-xs px-2 py-0.5 rounded font-bold">
                {st.station_code}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
