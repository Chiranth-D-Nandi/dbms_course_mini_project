"""Small measured HTTP workflow check, using only Python's standard library."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
from pathlib import Path
import random
import statistics
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4
from zoneinfo import ZoneInfo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='http://127.0.0.1:8000')
    parser.add_argument('--users', type=int, default=2)
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--output', default='docs/artifacts/load-smoke.json')
    args = parser.parse_args()
    samples, errors = [], []
    lock = threading.Lock()
    journey = (datetime.now(ZoneInfo('Asia/Kolkata')) + timedelta(days=3)).date().isoformat()

    def call(label, path, method='GET', payload=None, token=None, key=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if key:
            headers['Idempotency-Key'] = key
        request = Request(args.host.rstrip('/') + '/api' + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers, method=method)
        started = time.perf_counter()
        try:
            with urlopen(request, timeout=15) as response:
                status, body = response.status, json.loads(response.read())
        except HTTPError as exc:
            status, body = exc.code, json.loads(exc.read())
        except Exception as exc:
            status, body = 0, {'error': {'message': type(exc).__name__}}
        with lock:
            samples.append({'endpoint': label, 'status': status, 'ms': round((time.perf_counter()-started)*1000, 2)})
        return status, body

    def require(ok, label, status, body):
        if not ok:
            with lock:
                errors.append({'endpoint': label, 'status': status, 'message': body.get('error', {}).get('message', 'Unexpected response')})
        return ok

    def user(index):
        rng = random.Random(index)
        email = ['chiranth@example.com', 'jashruth@example.com', 'ramesh@example.com', 'priya@example.com', 'anand@example.com'][index % 5]
        status, body = call('login', '/auth/login', 'POST', {'email': email, 'password': 'Customer@123'})
        if not require(status == 200, 'login', status, body):
            return
        token = body['tokens']['access']
        search = f'/trains/search/?source=SBC&dest=MAS&date={journey}'
        status, body = call('search', search)
        if not require(status == 200 and bool(body.get('trains')), 'search', status, body):
            return
        rows = [r for r in body['trains'] if r['class_code'] == '3A']
        if not rows:
            require(False, 'search', status, {'error': {'message': 'Seed AC 3 Tier inventory first.'}})
            return
        run = rows[0]['run_id']
        source, dest = body['source']['station_id'], body['destination']['station_id']
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            action = rng.choice(['search', 'seat_map', 'booking'])
            if action == 'search':
                status, result = call('search', search)
                require(status in (200, 429), 'search', status, result)
            elif action == 'seat_map':
                status, result = call('seat_map', f'/runs/{run}/seats/?class=3A&quota=GENERAL')
                require(status in (200, 429), 'seat_map', status, result)
            else:
                payload = {'run_id': run, 'source_station_id': source, 'dest_station_id': dest, 'class_code': '3A', 'booking_type': 'GENERAL',
                    'passengers': [{'passenger_name': f'Load Smoke {index}', 'age': 28, 'gender': 'MALE', 'id_card_type': 'AADHAAR', 'id_card_number': '111122223333'}]}
                status, result = call('booking', '/bookings/', 'POST', payload, token)
                if status == 201:
                    pnr, key = result['booking']['pnr'], str(uuid4())
                    payment = {'pnr': pnr, 'payment_method': 'UPI'}
                    first_status, first = call('payment', '/payments/confirm/', 'POST', payment, token, key)
                    if require(first_status == 200, 'payment', first_status, first):
                        retry_status, retry = call('payment_retry', '/payments/confirm/', 'POST', payment, token, key)
                        require(retry_status == 200 and retry.get('payment', {}).get('transaction_id') == first['payment']['transaction_id'], 'payment_retry', retry_status, retry)
                        cancel_status, cancelled = call('cancel', f'/bookings/{pnr}/cancel/', 'POST', {'reason': 'Load smoke cleanup'}, token)
                        require(cancel_status == 200, 'cancel', cancel_status, cancelled)
                else:
                    sold_out = status == 409 and result.get('error', {}).get('details', {}).get('status') == 'SOLD_OUT'
                    require(status == 429 or sold_out, 'booking', status, result)
            time.sleep(0.5)

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, args.users)) as executor:
        list(executor.map(user, range(max(1, args.users))))
    latency = sorted(s['ms'] for s in samples)
    percentile = lambda p: latency[min(len(latency)-1, int((len(latency)-1)*p))] if latency else 0
    counts = {}
    for sample in samples:
        name = sample['endpoint']
        counts.setdefault(name, {'requests': 0, 'statuses': {}})
        counts[name]['requests'] += 1
        status = str(sample['status'])
        counts[name]['statuses'][status] = counts[name]['statuses'].get(status, 0) + 1
    result = {'timestamp_ist': datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(), 'users': args.users,
        'requested_seconds': args.seconds, 'elapsed_seconds': round(time.perf_counter()-started, 2),
        'requests': len(samples), 'unexpected_errors': len(errors), 'average_ms': round(statistics.mean(latency), 2) if latency else 0,
        'p95_ms': percentile(.95), 'p99_ms': percentile(.99), 'endpoints': counts, 'errors': errors,
        'scope': 'Local development-server smoke test; not a production capacity benchmark.'}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == '__main__':
    main()
