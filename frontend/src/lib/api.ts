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
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

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
    return this.request<User>('/auth/me');
  }

  // Stations & Trains
  async searchStations(q: string): Promise<Station[]> {
    return this.request<Station[]>(`/stations?q=${encodeURIComponent(q)}`);
  }

  async searchTrains(from: number, to: number, date: string): Promise<TrainSearchResult[]> {
    return this.request<TrainSearchResult[]>(`/trains/search?from=${from}&to=${to}&date=${date}`);
  }

  async getTrain(id: number): Promise<TrainDetail> {
    return this.request<TrainDetail>(`/trains/${id}`);
  }

  async getSeatMap(runId: number): Promise<SeatMapItem[]> {
    return this.request<SeatMapItem[]>(`/runs/${runId}/seats`);
  }

  async getTatkalStatus(runId: number, classCode: string): Promise<TatkalStatus> {
    return this.request<TatkalStatus>(`/tatkal/status?run_id=${runId}&class=${classCode}`);
  }

  // Booking
  async createBooking(payload: BookingCreatePayload): Promise<BookingResponse> {
    return this.request<BookingResponse>('/bookings', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async payBooking(pnr: number, payload: PaymentPayload, idempotencyKey: string): Promise<PaymentResponse> {
    return this.request<PaymentResponse>(
      `/bookings/${pnr}/pay`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      {
        'Idempotency-Key': idempotencyKey,
      }
    );
  }

  async cancelBooking(pnr: number, reason: string): Promise<any> {
    return this.request(`/bookings/${pnr}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async getMyBookings(): Promise<BookingDetail[]> {
    return this.request<BookingDetail[]>('/bookings/mine');
  }

  async getBooking(pnr: number): Promise<BookingDetail> {
    return this.request<BookingDetail>(`/bookings/${pnr}`);
  }

  // Chroma Vector Search
  async searchTrainsSemantic(q: string, trainType?: string): Promise<any[]> {
    const params = new URLSearchParams({ q });
    if (trainType) params.append('train_type', trainType);
    return this.request<any[]>(`/search/trains?${params.toString()}`);
  }

  async searchFaq(q: string, category?: string): Promise<FaqChunk[]> {
    const params = new URLSearchParams({ q });
    if (category) params.append('category', category);
    return this.request<FaqChunk[]>(`/search/faq?${params.toString()}`);
  }

  // Admin Endpoints
  async getAdminRevenue(): Promise<any[]> {
    return this.request<any[]>('/admin/reports/revenue');
  }

  async getAdminOccupancy(): Promise<any[]> {
    return this.request<any[]>('/admin/reports/occupancy');
  }

  async getAdminTatkalDemand(): Promise<any[]> {
    return this.request<any[]>('/admin/reports/tatkal-demand');
  }

  async getAdminAuditLog(): Promise<any[]> {
    return this.request<any[]>('/admin/audit-log');
  }
}

export const api = new ApiClient();
