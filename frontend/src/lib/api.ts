// Owner: Person B
import {
  AuthResponse,
  BookingCreatePayload,
  BookingDetail,
  BookingResponse,
  FaqChunk,
  PaymentPayload,
  PaymentResponse,
  SeatMapItem,
  Station,
  TatkalStatus,
  TrainDetail,
  TrainSearchResult,
  User,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

class ApiClient {
  private getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('tatkal_access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('tatkal_refresh_token');
  }

  public setTokens(access: string, refresh: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('tatkal_access_token', access);
      localStorage.setItem('tatkal_refresh_token', refresh);
    }
  }

  public clearTokens() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('tatkal_access_token');
      localStorage.removeItem('tatkal_refresh_token');
      localStorage.removeItem('tatkal_user');
    }
  }

  public getCurrentUser(): User | null {
    if (typeof window === 'undefined') return null;
    const raw = localStorage.getItem('tatkal_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  public setCurrentUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('tatkal_user', JSON.stringify(user));
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    customHeaders: Record<string, string> = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...customHeaders,
    };

    const token = this.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    let response = await fetch(url, { ...options, headers });

    // Handle 401 token refresh
    if (response.status === 401 && this.getRefreshToken()) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
        response = await fetch(url, { ...options, headers });
      } else {
        this.clearTokens();
      }
    }

    if (!response.ok) {
      let errorData = { error: { code: 'HTTP_ERROR', message: `Request failed with status ${response.status}` } };
      try {
        errorData = await response.json();
      } catch {}
      throw errorData;
    }

    return response.json();
  }

  private async refreshToken(): Promise<boolean> {
    const refresh = this.getRefreshToken();
    if (!refresh) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (data.access) {
        localStorage.setItem('tatkal_access_token', data.access);
        if (data.refresh) localStorage.setItem('tatkal_refresh_token', data.refresh);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  private normalizeBooking(row: any): BookingDetail {
    return {...row, pnr: Number(row.pnr), source_station: row.source?.name || '', dest_station: row.destination?.name || '',
      passengers: (row.passengers || []).map((p: any) => ({...p, passenger_seq: p.passenger_id, name: p.passenger_name, coach_number: p.coach_code, id_proof_type: p.id_card_type, id_proof_no: p.id_card_number, fare_amount: p.seat_fare})),
      payment: row.payments?.[0] ? {...row.payments[0], txn_ref: row.payments[0].transaction_id, method: row.payments[0].payment_method, status: row.payments[0].payment_status} : undefined};
  }

  async listTrains(): Promise<any[]> { return this.request<any[]>('/trains/'); }
  async createRun(trainId: number, journeyDate: string): Promise<any> {
    return this.request('/admin/runs/', {method: 'POST', body: JSON.stringify({train_id: trainId, journey_date: journeyDate})});
  }
  async releaseHolds(): Promise<any> { return this.request('/admin/release-holds/', {method: 'POST', body: '{}'}); }

  // Auth
  async register(payload: Record<string, any>): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setTokens(res.tokens.access, res.tokens.refresh);
    this.setCurrentUser(res.user);
    return res;
  }

  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setTokens(res.tokens.access, res.tokens.refresh);
    this.setCurrentUser(res.user);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<{user: User}>('/auth/me').then(r => r.user);
  }

  // Stations & Trains
  async searchStations(q: string): Promise<Station[]> {
    return this.request<Station[]>(`/stations/?q=${encodeURIComponent(q)}`);
  }

  async searchTrains(from: number, to: number, date: string): Promise<TrainSearchResult[]> {
    const res = await this.request<{trains: any[]}>(`/trains/search/?source=${from}&dest=${to}&date=${date}`);
    const grouped = new Map<number, TrainSearchResult>();
    for (const row of res.trains) {
      if (!grouped.has(row.run_id)) grouped.set(row.run_id, {...row, availability: []});
      grouped.get(row.run_id)!.availability.push({...row, base_fare: Number(row.base_fare), tatkal_fare: Number(row.tatkal_fare)});
    }
    return Array.from(grouped.values());
  }

  async getTrain(id: number): Promise<TrainDetail> {
    const row = await this.request<any>(`/trains/${id}/`);
    return {...row, stops: row.stops.map((s: any) => ({...s, stop_seq: s.stop_sequence, halt_duration_minutes: s.halt_duration_minutes || 0}))};
  }

  async getSeatMap(runId: number, classCode = '3A', quota = 'GENERAL'): Promise<SeatMapItem[]> {
    const row = await this.request<any>(`/runs/${runId}/seats/?class=${classCode}&quota=${quota}`);
    return row.coaches.flatMap((c: any) => c.seats.map((s: any) => ({...s, run_id: runId, coach_id: c.coach_id, coach_number: c.coach_code, class_code: c.class_code, quota_type: s.quota, seat_status: s.status})));
  }

  async getTatkalStatus(runId: number, classCode: string): Promise<TatkalStatus> {
    const row = await this.request<any>(`/tatkal/status/?run_id=${runId}&class=${classCode}`);
    return {...row, run_id: runId, tatkal_open_time: row.opens_at, is_open: row.status === 'OPEN'};
  }

  // Booking
  async createBooking(payload: BookingCreatePayload): Promise<BookingResponse> {
    const row = await this.request<any>('/bookings/', {
      method: 'POST',
      body: JSON.stringify({...payload, passengers: payload.passengers.map(p => ({passenger_name: p.name, dob: p.dob, gender: p.gender, id_card_type: p.id_proof_type, id_card_number: p.id_proof_no}))}),
    });
    return {...row.booking, pnr: Number(row.booking.pnr), status: 'PENDING', message: row.message};
  }

  async payBooking(pnr: number, payload: PaymentPayload, idempotencyKey: string): Promise<PaymentResponse> {
    return this.request<PaymentResponse>(
      '/payments/confirm/',
      {
        method: 'POST',
        body: JSON.stringify({pnr, payment_method: payload.method, idempotency_key: idempotencyKey}),
      },
      {
        'Idempotency-Key': idempotencyKey,
      }
    );
  }

  async cancelBooking(pnr: number, reason: string): Promise<any> {
    return this.request(`/bookings/${pnr}/cancel/`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async getMyBookings(): Promise<BookingDetail[]> {
    return this.request<any[]>('/bookings/my/').then(rows => rows.map(row => this.normalizeBooking(row)));
  }

  async getBooking(pnr: number): Promise<BookingDetail> {
    return this.request<any>(`/bookings/${pnr}/`).then(row => this.normalizeBooking(row));
  }

  // Chroma Vector Search
  async searchTrainsSemantic(q: string, trainType?: string): Promise<any[]> {
    const params = new URLSearchParams({ q });
    if (trainType) params.append('train_type', trainType);
    return this.request<{results: any[]}>(`/search/trains/?${params.toString()}`).then(r => r.results);
  }

  async searchFaq(q: string, category?: string): Promise<FaqChunk[]> {
    const params = new URLSearchParams({ q });
    if (category) params.append('category', category);
    return this.request<{results: FaqChunk[]}>(`/search/faq/?${params.toString()}`).then(r => r.results);
  }

  // Admin Endpoints
  async getAdminRevenue(): Promise<any[]> {
    return this.request<any>('/admin/revenue/').then(r => r.revenue_data.map((x: any) => ({...x, total_revenue: x.gross_revenue, confirmed_bookings: x.total_confirmed_tickets, cancellations: x.total_cancellations})));
  }

  async getAdminOccupancy(): Promise<any[]> {
    return this.request<any[]>('/admin/reports/occupancy/');
  }

  async getAdminTatkalDemand(): Promise<any[]> {
    return this.request<any[]>('/admin/reports/tatkal-demand/');
  }

  async getAdminAuditLog(): Promise<any[]> {
    return this.request<any[]>('/admin/audit-logs/').then(rows => rows.map(r => ({...r, table_name: r.entity_name, record_id: r.entity_id, old_value: r.old_state, new_value: r.new_state})));
  }
}

export const api = new ApiClient();
