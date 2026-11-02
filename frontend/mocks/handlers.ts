// Owner: Person B
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Stations autocomplete
  http.get('*/api/stations', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q') || '';
    const stations = [
      { station_id: 1, station_code: 'SBC', station_name: 'KSR Bengaluru City', city: 'Bengaluru', state: 'Karnataka' },
      { station_id: 2, station_code: 'MAS', station_name: 'Chennai Central', city: 'Chennai', state: 'Tamil Nadu' },
      { station_id: 3, station_code: 'NDLS', station_name: 'New Delhi', city: 'New Delhi', state: 'Delhi' },
      { station_id: 4, station_code: 'MMCT', station_name: 'Mumbai Central', city: 'Mumbai', state: 'Maharashtra' },
      { station_id: 5, station_code: 'HWH', station_name: 'Howrah Junction', city: 'Kolkata', state: 'West Bengal' },
    ];
    const filtered = stations.filter(
      (s) =>
        s.station_code.toLowerCase().includes(q.toLowerCase()) ||
        s.station_name.toLowerCase().includes(q.toLowerCase()) ||
        s.city.toLowerCase().includes(q.toLowerCase())
    );
    return HttpResponse.json(filtered);
  }),

  // Search trains
  http.get('*/api/trains/search', () => {
    return HttpResponse.json([
      {
        run_id: 101,
        train_id: 1,
        train_number: '12658',
        train_name: 'Bengaluru - Chennai Mail',
        train_type: 'SUPERFAST',
        source_departure: '22:40:00',
        dest_arrival: '04:15:00',
        distance_km: 362,
        journey_date: '2026-11-05',
        availability: [
          {
            class_code: '3A',
            class_name: 'AC 3 Tier',
            general_available: 24,
            tatkal_available: 8,
            base_fare: 680,
            tatkal_fare: 880,
          },
          {
            class_code: 'SL',
            class_name: 'Sleeper',
            general_available: 48,
            tatkal_available: 12,
            base_fare: 240,
            tatkal_fare: 340,
          },
        ],
      },
    ]);
  }),

  // Train detail
  http.get('*/api/trains/:id', ({ params }) => {
    return HttpResponse.json({
      train_id: Number(params.id),
      train_number: '12658',
      train_name: 'Bengaluru - Chennai Mail',
      train_type: 'SUPERFAST',
      total_coaches: 18,
      running_days: [0, 1, 2, 3, 4, 5, 6],
      stops: [
        { stop_seq: 1, station_id: 1, station_code: 'SBC', station_name: 'KSR Bengaluru City', arrival_time: null, departure_time: '22:40:00', distance_km: 0, halt_duration_minutes: 0 },
        { stop_seq: 2, station_id: 2, station_code: 'BWT', station_name: 'Bangarapet', arrival_time: '23:43:00', departure_time: '23:45:00', distance_km: 70, halt_duration_minutes: 2 },
        { stop_seq: 3, station_id: 3, station_code: 'KPD', station_name: 'Katpadi Junction', arrival_time: '02:08:00', departure_time: '02:10:00', distance_km: 232, halt_duration_minutes: 2 },
        { stop_seq: 4, station_id: 4, station_code: 'MAS', station_name: 'Chennai Central', arrival_time: '04:15:00', departure_time: null, distance_km: 362, halt_duration_minutes: 0 },
      ],
    });
  }),

  // Tatkal status
  http.get('*/api/tatkal/status', () => {
    return HttpResponse.json({
      run_id: 101,
      class_code: '3A',
      journey_date: '2026-11-05',
      tatkal_open_time: '2026-11-04T10:00:00',
      is_open: true,
      seconds_remaining: 0,
      quota_total: 16,
      quota_available: 8,
    });
  }),

  // Book seats
  http.post('*/api/bookings', async () => {
    return HttpResponse.json(
      {
        pnr: 1000000042,
        status: 'PENDING',
        total_fare: 880,
        booking_time: new Date().toISOString(),
        expires_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
        hold_seconds_remaining: 300,
        message: 'Seats held successfully. Complete payment within 5 minutes.',
      },
      { status: 201 }
    );
  }),

  // Confirm payment
  http.post('*/api/bookings/:pnr/pay', async () => {
    return HttpResponse.json({
      payment_id: 301,
      pnr: 1000000042,
      txn_ref: 'TXN_MOCK_20261102_9871',
      status: 'SUCCESS',
      booking_status: 'CONFIRMED',
      message: 'Payment confirmed. Ticket issued!',
    });
  }),

  // Semantic search faq
  http.get('*/api/search/faq', () => {
    return HttpResponse.json([
      {
        chunk_id: 'faq-1',
        category: 'TATKAL_RULES',
        title: 'Tatkal Booking Window Timings',
        content: 'Tatkal booking opens at 10:00 AM for AC classes (1A, 2A, 3A, CC) and at 11:00 AM for Non-AC classes (SL) on the day prior to train departure.',
        similarity_score: 0.94,
      },
      {
        chunk_id: 'faq-2',
        category: 'CANCELLATION',
        title: 'Tatkal Ticket Cancellation and Refunds',
        content: 'Under Indian Railways regulations, no refund is granted on cancellation of confirmed Tatkal tickets.',
        similarity_score: 0.89,
      },
    ]);
  }),
];
