'use client';

import { useEffect, useState, useCallback, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { BookingDetail, PassengerInput, SeatMapItem, TatkalStatus, TrainDetail } from '@/lib/types';
import SeatMap from './SeatMap';
import RouteTimeline from './RouteTimeline';
import TatkalCountdown from './TatkalCountdown';

const field = 'w-full rounded-lg border border-slate-300 bg-white p-2.5 text-sm';
const button = 'rounded-lg bg-[#0f2e5a] px-5 py-3 text-sm font-bold text-white disabled:opacity-50';
const message = (e: any) => e?.error?.message || e?.message || 'Unable to complete this request.';
const blankPassenger = (): PassengerInput => ({name: '', dob: '', gender: 'MALE', id_proof_type: 'AADHAAR', id_proof_no: ''});
// Database timestamps are Indian local time. Never interpret them as the browser's local timezone.
const instant = (value: string) => new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}+05:30`).getTime();

function Frame({title, children}: {title: string; children: React.ReactNode}) {
  return <section className="mx-auto max-w-5xl space-y-6 px-4 py-10"><Link className="text-sm text-blue-700" href="/search">← Search trains</Link><h1 className="text-3xl font-black text-slate-900">{title}</h1>{children}</section>;
}
function ErrorBox({error}: {error: string}) {
  return error ? <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</p> : null;
}

export function BookingForm({runId}: {runId: number}) {
  const router = useRouter();
  const [config, setConfig] = useState({classCode: '3A', quota: 'GENERAL', src: 0, dst: 0});
  const [passengers, setPassengers] = useState<PassengerInput[]>([blankPassenger()]);
  const [seats, setSeats] = useState<SeatMapItem[]>([]);
  const [tatkal, setTatkal] = useState<TatkalStatus | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!api.getCurrentUser()) { router.replace(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`); return; }
    const q = new URLSearchParams(window.location.search);
    const c = {classCode: q.get('class') || '3A', quota: q.get('type') === 'TATKAL' ? 'TATKAL' : 'GENERAL', src: Number(q.get('src')), dst: Number(q.get('dst'))};
    setConfig(c);
    if (!c.src || !c.dst) { setError('Select a route from the train search results before booking.'); return; }
    Promise.all([api.getSeatMap(runId, c.classCode, c.quota), api.getTatkalStatus(runId, c.classCode)])
      .then(([s, t]) => {setSeats(s); setTatkal(t); setReady(true);}).catch(e => setError(message(e)));
  }, [runId, router]);
  const update = (index: number, key: keyof PassengerInput, value: string) => setPassengers(rows => rows.map((row, i) => i === index ? {...row, [key]: value} : row));
  const refreshWindow = useCallback(() => {api.getTatkalStatus(runId, config.classCode).then(setTatkal).catch(e => setError(message(e)));}, [runId, config.classCode]);
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const booking = await api.createBooking({run_id: runId, class_code: config.classCode, source_station_id: config.src, dest_station_id: config.dst, booking_type: config.quota as 'GENERAL' | 'TATKAL', passengers});
      router.push(`/pay/${booking.pnr}`);
    } catch (e) {setError(message(e));} finally {setBusy(false);}
  }
  return <Frame title="Book tickets"><ErrorBox error={error}/>
    <p className="text-slate-600">Run #{runId} · {config.classCode} · {config.quota}. Seats are assigned automatically when you reserve. Payment is a demo simulation.</p>
    {config.quota === 'TATKAL' && tatkal && <TatkalCountdown secondsRemaining={tatkal.seconds_remaining} isOpen={tatkal.is_open} tatkalOpenTime={tatkal.tatkal_open_time} onWindowOpen={refreshWindow}/>}
    {ready && <SeatMap seats={seats} selectedClass={config.classCode}/>}
    <form onSubmit={submit} className="space-y-5"><h2 className="text-xl font-bold">Passenger details</h2>
      {passengers.map((p, i) => <fieldset key={i} className="rounded-xl border bg-white p-5"><legend className="px-2 font-bold">Passenger {i + 1}</legend><div className="grid gap-4 sm:grid-cols-2">
        <label>Full name<input aria-label={`Passenger ${i+1} name`} className={field} value={p.name} required maxLength={100} onChange={e => update(i, 'name', e.target.value)}/></label>
        <label>Date of birth<input aria-label={`Passenger ${i+1} date of birth`} className={field} type="date" value={p.dob} required max={new Date(new Date().setFullYear(new Date().getFullYear()-1)).toISOString().slice(0,10)} onChange={e => update(i, 'dob', e.target.value)}/></label>
        <label>Gender<select className={field} value={p.gender} onChange={e => update(i, 'gender', e.target.value)}><option>MALE</option><option>FEMALE</option><option>OTHER</option></select></label>
        <label>ID type<select className={field} value={p.id_proof_type} onChange={e => update(i, 'id_proof_type', e.target.value)}>{['AADHAAR','PAN','PASSPORT','VOTER_ID'].map(v => <option key={v}>{v}</option>)}</select></label>
        <label>ID number<input aria-label={`Passenger ${i+1} ID number`} className={field} value={p.id_proof_no} required maxLength={50} onChange={e => update(i, 'id_proof_no', e.target.value)}/></label>
      </div>{passengers.length > 1 && <button type="button" className="mt-3 text-red-700" onClick={() => setPassengers(rows => rows.filter((_, n) => n !== i))}>Remove passenger</button>}</fieldset>)}
      <div className="flex flex-wrap gap-4"><button type="button" className="rounded-lg border bg-white px-4 py-2" disabled={passengers.length >= (config.quota === 'TATKAL' ? 4 : 6)} onClick={() => setPassengers(rows => [...rows, blankPassenger()])}>Add passenger</button>
      <button className={button} disabled={!ready || busy || (config.quota === 'TATKAL' && !tatkal?.is_open)}>{busy ? 'Reserving…' : 'Reserve seats for 8 minutes'}</button></div>
    </form></Frame>;
}

export function TicketPage({pnr, payment = false}: {pnr: number; payment?: boolean}) {
  const router = useRouter();
  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [method, setMethod] = useState<'UPI' | 'CARD' | 'NETBANKING'>('UPI');
  const [reason, setReason] = useState('');
  useEffect(() => {
    if (!api.getCurrentUser()) {router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`); return;}
    let active = true;
    const load = () => api.getBooking(pnr).then(b => {if (active) setBooking(b);}).catch(e => {if (active) setError(message(e));});
    load(); const poll = setInterval(load, 15000);
    return () => {active = false; clearInterval(poll);};
  }, [pnr, router]);
  useEffect(() => {
    const tick = () => setSeconds(booking?.expires_at ? Math.max(0, Math.ceil((instant(booking.expires_at) - Date.now()) / 1000)) : 0);
    tick(); const timer = setInterval(tick, 1000); return () => clearInterval(timer);
  }, [booking]);
  async function pay() {
    if (!booking) return;
    setBusy(true); setError('');
    const storageKey = `tatkal_payment_${pnr}_${method}`;
    let key = sessionStorage.getItem(storageKey);
    if (!key) {key = crypto.randomUUID(); sessionStorage.setItem(storageKey, key);}
    try {await api.payBooking(pnr, {amount: booking.total_fare, method}, key); setBooking(await api.getBooking(pnr)); router.replace(`/bookings/${pnr}`);}
    catch (e) {setError(message(e));} finally {setBusy(false);}
  }
  async function cancel() {
    setBusy(true); setError('');
    try {await api.cancelBooking(pnr, reason); setBooking(await api.getBooking(pnr));}
    catch (e) {setError(message(e));} finally {setBusy(false);}
  }
  return <Frame title={payment ? 'Complete payment' : 'Your e-ticket'}><ErrorBox error={error}/>
    {!booking ? <p>Loading booking…</p> : <>
      <article className="space-y-4 rounded-2xl border bg-white p-6"><div className="flex flex-wrap justify-between gap-3"><h2 className="text-xl font-bold">PNR #{booking.pnr}</h2><strong role="status">{booking.status}</strong></div>
      <p className="font-bold">{booking.train_name} · #{booking.train_number}</p><p>{booking.source_station} → {booking.dest_station}</p><p>{booking.journey_date} · {booking.class_code} · {booking.booking_type}</p><p className="text-xl font-bold">Total fare: ₹{booking.total_fare}</p>
      {booking.status === 'PENDING' && <p className="rounded-lg bg-amber-50 p-3" role="timer">{seconds > 0 ? `Seat hold: ${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')} remaining` : 'Hold expired. These seats can no longer be paid for.'}</p>}
      <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="py-2">Passenger</th><th>ID type</th><th>Coach / seat</th><th>Berth</th></tr></thead><tbody>{booking.passengers.map((p,i) => <tr key={i} className="border-t"><td className="py-3">{p.name}</td><td>{p.id_proof_type}</td><td>{p.coach_number || '—'} / {p.seat_number || '—'}</td><td>{p.berth_type || '—'}</td></tr>)}</tbody></table></div>
      {booking.payment && <p>Payment: {booking.payment.txn_ref} · {booking.payment.method}</p>}
      {booking.cancellation && <p className="rounded-lg bg-slate-100 p-3">Cancelled · Refund: ₹{booking.cancellation.refund_amount} · {booking.cancellation.reason}</p>}
      </article>
      {booking.status === 'PENDING' && seconds > 0 && <div className="space-y-4 rounded-xl border bg-white p-5"><p>Demo payment only. No money is charged.</p><label>Payment method<select className={field} value={method} onChange={e => setMethod(e.target.value as typeof method)}><option>UPI</option><option>CARD</option><option>NETBANKING</option></select></label><button className={button} disabled={busy} onClick={pay}>{busy ? 'Processing…' : `Confirm & pay ₹${booking.total_fare}`}</button></div>}
      {booking.status === 'CONFIRMED' && <form className="space-y-3 rounded-xl border bg-white p-5" onSubmit={e => {e.preventDefault(); cancel();}}><h2 className="font-bold">Cancel ticket</h2><p className="text-sm text-slate-600">Demo policy: General refunds are 90% above 48 hours, 50% at 12–48 hours, 25% at 4–12 hours and zero below 4 hours. Confirmed Tatkal has no refund.</p><label>Reason<input className={field} value={reason} maxLength={500} onChange={e => setReason(e.target.value)}/></label><button disabled={busy} className="rounded-lg bg-red-700 px-4 py-2 text-white">{busy ? 'Cancelling…' : 'Cancel confirmed ticket'}</button><button type="button" className="ml-4 text-blue-700" onClick={() => window.print()}>Print ticket</button></form>}
      <Link className="inline-block text-blue-700" href="/bookings">View all my bookings →</Link>
    </>}
  </Frame>;
}

export function TrainPage({trainId}: {trainId: number}) {
  const [train, setTrain] = useState<TrainDetail | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {api.getTrain(trainId).then(setTrain).catch(e => setError(message(e)));}, [trainId]);
  return <Frame title={train?.train_name || 'Train timetable'}><ErrorBox error={error}/>{train && <><p>#{train.train_number} · {train.train_type} · {train.total_coaches} coaches</p><p>Runs: {train.running_days.map(d => ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d]).join(', ')}</p><div className="rounded-xl border bg-white p-6"><RouteTimeline stops={train.stops}/></div></>}</Frame>;
}
