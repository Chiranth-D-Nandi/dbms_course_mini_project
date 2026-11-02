// Owner: Person B
export type UserRole = 'ADMIN' | 'CUSTOMER';

export interface User {
  user_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: UserRole;
  created_at?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface Station {
  station_id: number;
  station_code: string;
  station_name: string;
  city: string;
  state: string;
}

export interface ClassAvailability {
  class_code: string;
  class_name: string;
  is_ac: boolean;
  general_available: number;
  tatkal_available: number;
  base_fare: number;
  tatkal_fare: number;
}

export interface TrainSearchResult {
  run_id: number;
  train_id: number;
  train_number: string;
  train_name: string;
  train_type: string;
  source_departure: string;
  dest_arrival: string;
  distance_km: number;
  journey_date: string;
  availability: ClassAvailability[];
}

export interface TrainStop {
  stop_seq: number;
  station_id: number;
  station_code: string;
  station_name: string;
  arrival_time: string | null;
  departure_time: string | null;
  day_offset: number;
  distance_km: number;
  halt_duration_minutes: number;
}

export interface TrainDetail {
  train_id: number;
  train_number: string;
  train_name: string;
  train_type: string;
  is_active: boolean;
  total_coaches: number;
  running_days: number[];
  stops: TrainStop[];
}

export interface TatkalStatus {
  run_id: number;
  class_code: string;
  journey_date: string;
  tatkal_open_time: string;
  is_open: boolean;
  seconds_remaining: number;
  quota_total: number;
  quota_available: number;
}

export interface SeatMapItem {
  run_id: number;
  seat_id: number;
  coach_id: number;
  coach_number: string;
  class_code: string;
  seat_number: number;
  berth_type: string;
  quota_type: 'GENERAL' | 'TATKAL';
  seat_status: 'AVAILABLE' | 'HELD' | 'BOOKED';
}

export interface PassengerInput {
  name: string;
  dob: string;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  id_proof_type: 'AADHAAR' | 'PAN' | 'PASSPORT' | 'VOTER_ID';
  id_proof_no: string;
}

export interface BookingCreatePayload {
  run_id: number;
  class_code: string;
  source_station_id: number;
  dest_station_id: number;
  booking_type: 'GENERAL' | 'TATKAL';
  passengers: PassengerInput[];
}

export interface BookingResponse {
  pnr: number;
  status: 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'EXPIRED' | 'FAILED';
  total_fare: number;
  booking_time: string;
  expires_at: string;
  hold_seconds_remaining: number;
  message?: string;
}

export interface PaymentPayload {
  amount: number;
  method: 'UPI' | 'CARD' | 'NETBANKING';
}

export interface PaymentResponse {
  payment_id: number;
  pnr: number;
  txn_ref: string;
  status: 'SUCCESS' | 'FAILED' | 'REFUNDED';
  booking_status: string;
  message: string;
}

export interface BookingPassenger {
  passenger_seq: number;
  name: string;
  dob: string;
  age: number;
  gender: string;
  id_proof_type: string;
  id_proof_no: string;
  fare_amount: number;
  status: string;
  coach_number?: string;
  seat_number?: number;
  berth_type?: string;
}

export interface BookingDetail {
  pnr: number;
  user_id: number;
  run_id: number;
  train_number: string;
  train_name: string;
  source_station: string;
  dest_station: string;
  journey_date: string;
  class_code: string;
  booking_type: 'GENERAL' | 'TATKAL';
  status: 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'EXPIRED' | 'FAILED';
  booking_time: string;
  expires_at: string | null;
  total_fare: number;
  passengers: BookingPassenger[];
  payment?: {
    payment_id: number;
    amount: number;
    method: string;
    status: string;
    txn_ref: string;
  };
  cancellation?: {
    cancellation_id: number;
    cancelled_at: string;
    refund_amount: number;
    reason: string;
  };
}

export interface FaqChunk {
  chunk_id: string;
  category: string;
  title: string;
  content: string;
  similarity_score?: number;
}
