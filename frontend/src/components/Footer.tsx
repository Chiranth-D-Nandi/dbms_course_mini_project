// Owner: Person B
import Link from 'next/link';
import { Train, Phone, ShieldCheck, Mail, MapPin } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-[#0a192f] text-slate-400 text-xs border-t border-slate-800 mt-auto">
      {/* Upper Navigation & Information Links */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Brand & Portal Info */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <div className="bg-amber-500 p-1.5 rounded-lg text-[#0f2e5a]">
              <Train className="w-5 h-5 stroke-[2.2]" />
            </div>
            <span className="font-black text-base text-white tracking-tight">
              TATKAL<span className="text-amber-400">EXPRESS</span>
            </span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Next-Generation High-Concurrency Passenger Reservation &amp; Tatkal Booking Engine with serialized berth locks and instant cancellation credit.
          </p>
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-1">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Centre for Railway Information Systems (CRIS)</span>
          </div>
        </div>

        {/* Quick Railway Portals */}
        <div className="space-y-2.5">
          <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider">
            Booking &amp; Services
          </h4>
          <ul className="space-y-1.5 text-[11px]">
            <li>
              <Link href="/search" className="hover:text-amber-400 transition">
                Search &amp; Book Train Tickets
              </Link>
            </li>
            <li>
              <Link href="/help" className="hover:text-amber-400 transition">
                Tatkal Booking Timings &amp; Rules
              </Link>
            </li>
            <li>
              <Link href="/bookings" className="hover:text-amber-400 transition">
                Electronic Reservation Slip (ERS)
              </Link>
            </li>
            <li>
              <Link href="/help" className="hover:text-amber-400 transition">
                Cancellation &amp; Refund Policy
              </Link>
            </li>
          </ul>
        </div>

        {/* Tatkal Opening Advisory */}
        <div className="space-y-2.5">
          <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider">
            Daily Tatkal Windows
          </h4>
          <div className="space-y-2 text-[11px]">
            <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700">
              <span className="font-bold text-amber-400 block">AC Classes (1A, 2A, 3A, CC)</span>
              <span className="text-slate-300">Opens at 10:00 AM IST Daily</span>
            </div>
            <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700">
              <span className="font-bold text-blue-400 block">Non-AC Classes (SL, 2S)</span>
              <span className="text-slate-300">Opens at 11:00 AM IST Daily</span>
            </div>
          </div>
        </div>

        {/* Customer Care & Helplines */}
        <div className="space-y-2.5">
          <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider">
            Railway Help &amp; Support
          </h4>
          <ul className="space-y-2 text-[11px]">
            <li className="flex items-center gap-2">
              <Phone className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>
                Rail Madad: <strong>139</strong> (24x7 All India)
              </span>
            </li>
            <li className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span>Security Helpline: <strong>182</strong></span>
            </li>
            <li className="flex items-center gap-2">
              <Mail className="w-3.5 h-3.5 text-blue-400 shrink-0" />
              <span>care@tatkalexpress.gov.in</span>
            </li>
          </ul>
        </div>
      </div>

      {/* College Project & Team Attribution Strip */}
      <div className="border-t border-slate-800/80 bg-[#06101e] py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-3 text-[11px]">
          <div>
            <span className="font-bold text-slate-300">
              DBMS Level 3 Experiential Learning Project
            </span>{' '}
            &bull; PES University &bull; MySQL 8.0 ACID + ChromaDB Semantic Retrieval
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div>
              <strong className="text-slate-200">Chiranth D Nandi</strong> (PES2UG24AM048) &mdash; Data &amp; Backend
            </div>
            <span className="text-slate-600 hidden sm:inline">&bull;</span>
            <div>
              <strong className="text-slate-200">Jashruth K A</strong> (PES2UG24AM069) &mdash; Experience &amp; Ops
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
