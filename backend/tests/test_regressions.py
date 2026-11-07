"""Regression tests for authorization, retries, inventory reuse, and financial totals."""
import uuid
from decimal import Decimal
import pytest
from django.db import connections
from booking_engine.models import AppUser
from booking_engine.auth_views import get_tokens_for_user

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "readonly"])


def hold(client, headers, run, stops):
    result = client.post('/api/bookings/', {
        'run_id': run, 'source_station_id': stops['source_id'], 'dest_station_id': stops['dest_id'],
        'class_code': '3A', 'booking_type': 'GENERAL', 'passengers': [{
            'passenger_name': 'Regression Passenger', 'age': 28, 'gender': 'MALE',
            'id_card_type': 'AADHAAR', 'id_card_number': '123456789012'}]}, format='json', **headers)
    assert result.status_code == 201, result.data
    return result.data['booking']


def pay(client, headers, pnr, key=None):
    return client.post('/api/payments/confirm/', {'pnr': pnr, 'payment_method': 'UPI'}, format='json',
                       HTTP_IDEMPOTENCY_KEY=key or str(uuid.uuid4()), **headers)


def test_public_admin_registration_rejected(api_client):
    result = api_client.post('/api/auth/register', {'first_name': 'Attacker', 'last_name': 'Test',
        'email': 'attacker@example.com', 'phone': '9000011111', 'password': 'Password123', 'role': 'ADMIN'}, format='json')
    assert result.status_code == 400
    assert not AppUser.objects.filter(email='attacker@example.com').exists()


def test_customer_registration_login_refresh(api_client):
    response = api_client.post('/api/auth/register', {'first_name': 'New', 'last_name': 'Customer',
        'email': 'new@example.com', 'phone': '9000011112', 'password': 'Password123'}, format='json')
    assert response.status_code == 201, response.data
    assert response.data['user']['role'] == 'CUSTOMER'
    refresh = api_client.post('/api/auth/refresh', {'refresh': response.data['tokens']['refresh']}, format='json')
    assert refresh.status_code == 200
    assert refresh.data['access']


def test_payment_requires_owner_and_valid_key(api_client, customer_auth_headers, sample_run_id, sample_stations):
    booking = hold(api_client, customer_auth_headers, sample_run_id, sample_stations)
    other = AppUser.objects.get(email='jashruth@example.com')
    headers = {'HTTP_AUTHORIZATION': 'Bearer ' + get_tokens_for_user(other)['access']}
    assert pay(api_client, headers, booking['pnr']).status_code == 403
    missing = api_client.post('/api/payments/confirm/', {'pnr': booking['pnr'], 'payment_method': 'UPI'}, format='json', **customer_auth_headers)
    assert missing.status_code == 400
    assert pay(api_client, customer_auth_headers, 'not-a-pnr').status_code == 400


def test_payment_key_is_bound_to_request(api_client, customer_auth_headers, sample_run_id, sample_stations):
    first = hold(api_client, customer_auth_headers, sample_run_id, sample_stations)
    second = hold(api_client, customer_auth_headers, sample_run_id, sample_stations)
    key = str(uuid.uuid4())
    response = pay(api_client, customer_auth_headers, first['pnr'], key)
    assert response.status_code == 200, response.data
    retry = pay(api_client, customer_auth_headers, first['pnr'], key)
    assert retry.status_code == 200
    assert response.data['payment']['transaction_id'] == retry.data['payment']['transaction_id']
    conflict = pay(api_client, customer_auth_headers, second['pnr'], key)
    assert conflict.status_code == 400, conflict.data
    assert api_client.get(f"/api/bookings/{second['pnr']}/", **customer_auth_headers).data['status'] == 'PENDING'
    assert api_client.post(f"/api/bookings/{first['pnr']}/cancel/", {}, format='json', **customer_auth_headers).status_code == 200
    assert pay(api_client, customer_auth_headers, first['pnr'], key).data['booking']['status'] == 'CANCELLED'


def test_tatkal_window_limits_and_zero_refund(api_client, customer_auth_headers, sample_run_id, sample_stations):
    payload = {'run_id': sample_run_id, 'source_station_id': sample_stations['source_id'],
        'dest_station_id': sample_stations['dest_id'], 'class_code':'3A', 'booking_type':'TATKAL',
        'passengers':[{'passenger_name':'Tatkal Test','age':28,'gender':'MALE','id_card_type':'AADHAAR','id_card_number':'123456789012'}]}
    closed = api_client.post('/api/bookings/', payload, format='json', **customer_auth_headers)
    assert closed.status_code == 409, closed.data
    assert closed.data['error']['details']['status'] == 'TATKAL_WINDOW_CLOSED'
    too_many = api_client.post('/api/bookings/', dict(payload, passengers=payload['passengers']*5), format='json', **customer_auth_headers)
    assert too_many.status_code == 400
    # Only direct SQL in this disposable test schema can enable the demo bypass.
    with connections['default'].cursor() as c:
        c.execute('SET @DEMO_BYPASS_TATKAL_WINDOW=1')
    try:
        result = api_client.post('/api/bookings/', payload, format='json', **customer_auth_headers)
    finally:
        with connections['default'].cursor() as c:
            c.execute('SET @DEMO_BYPASS_TATKAL_WINDOW=0')
    assert result.status_code == 201, result.data
    pnr = result.data['booking']['pnr']
    assert pay(api_client, customer_auth_headers, pnr).status_code == 200
    cancelled = api_client.post(f'/api/bookings/{pnr}/cancel/', {}, format='json', **customer_auth_headers)
    assert cancelled.status_code == 200, cancelled.data
    assert cancelled.data['cancellation']['refund_amount'] == 0


@pytest.mark.parametrize('dob', ['2100-01-01', '1800-01-01'])
def test_passenger_date_of_birth_validation(api_client, customer_auth_headers, sample_run_id, sample_stations, dob):
    result = api_client.post('/api/bookings/', {'run_id':sample_run_id,'source_station_id':sample_stations['source_id'],
        'dest_station_id':sample_stations['dest_id'],'class_code':'3A','booking_type':'GENERAL',
        'passengers':[{'passenger_name':'Invalid DOB','dob':dob,'gender':'MALE','id_card_type':'PAN','id_card_number':'DEMO123'}]}, format='json', **customer_auth_headers)
    assert result.status_code == 400


@pytest.mark.parametrize('via_payment', [True, False])
def test_expired_seats_are_reusable(api_client, customer_auth_headers, admin_auth_headers, sample_run_id, sample_stations, via_payment):
    booking = hold(api_client, customer_auth_headers, sample_run_id, sample_stations)
    with connections['default'].cursor() as c:
        c.execute('SELECT TIMESTAMPDIFF(SECOND, booking_time, expires_at) FROM booking WHERE pnr=%s', [booking['pnr']])
        assert c.fetchone()[0] == 480
        c.execute('SELECT seat_id FROM passenger WHERE pnr=%s', [booking['pnr']])
        seat = c.fetchone()[0]
        c.execute('UPDATE booking SET expires_at=NOW()-INTERVAL 1 SECOND WHERE pnr=%s', [booking['pnr']])
        c.execute('UPDATE run_seat SET hold_expires_at=NOW()-INTERVAL 1 SECOND WHERE held_by_pnr=%s', [booking['pnr']])
    if via_payment:
        assert pay(api_client, customer_auth_headers, booking['pnr']).status_code == 400
    else:
        sweep = api_client.post('/api/admin/release-holds/', {}, format='json', **admin_auth_headers)
        assert sweep.status_code == 200, sweep.data
    with connections['default'].cursor() as c:
        c.execute('SELECT status FROM booking WHERE pnr=%s', [booking['pnr']])
        assert c.fetchone()[0] == 'EXPIRED'
        c.execute('SELECT run_id,seat_id FROM passenger WHERE pnr=%s', [booking['pnr']])
        assert c.fetchone() == (None, None)
        c.execute('SELECT seat_status FROM run_seat WHERE run_id=%s AND seat_id=%s', [sample_run_id, seat])
        assert c.fetchone()[0] == 'AVAILABLE'
    hold(api_client, customer_auth_headers, sample_run_id, sample_stations)


def test_revenue_matches_receipts_and_refunds():
    with connections['readonly'].cursor() as c:
        c.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE status IN ('SUCCESS','REFUNDED')")
        gross = c.fetchone()[0]
        c.execute('SELECT COALESCE(SUM(refund_amount),0) FROM cancellation')
        refunds = c.fetchone()[0]
        c.execute('SELECT SUM(total_revenue),SUM(total_refunds),SUM(net_revenue) FROM v_admin_revenue')
        assert c.fetchone() == (gross, refunds, gross-refunds)


def test_readonly_account_cannot_execute_mutating_procedures():
    from django.db import DatabaseError
    with connections['readonly'].cursor() as cursor:
        with pytest.raises(DatabaseError):
            cursor.execute('CALL sp_release_expired_holds()')


def test_admin_schedules_run_and_inventory(api_client, admin_auth_headers, customer_auth_headers):
    from datetime import date, timedelta
    payload = {'train_id': 1, 'journey_date': (date.today()+timedelta(days=20)).isoformat()}
    assert api_client.post('/api/admin/runs/', payload, format='json', **customer_auth_headers).status_code == 403
    response = api_client.post('/api/admin/runs/', payload, format='json', **admin_auth_headers)
    assert response.status_code == 201, response.data
    with connections['readonly'].cursor() as c:
        c.execute('SELECT COUNT(*) FROM run_seat WHERE run_id=%s', [response.data['run_id']])
        assert c.fetchone()[0] > 0
    assert api_client.post('/api/admin/runs/', payload, format='json', **admin_auth_headers).status_code == 409


@pytest.mark.parametrize('hours,ratio', [(72, '0.90'), (24, '0.50'), (8, '0.25'), (2, '0')])
def test_refund_tiers(api_client, customer_auth_headers, sample_stations, hours, ratio):
    from datetime import timedelta
    with connections['default'].cursor() as c:
        c.execute('SELECT NOW()')
        departure = c.fetchone()[0] + timedelta(hours=hours, minutes=1)
        c.execute("INSERT INTO train(train_number,train_name,train_type) VALUES (%s,'Refund regression','EXPRESS')", ['R'+uuid.uuid4().hex[:8]])
        train = c.lastrowid
        c.execute('INSERT INTO train_stop(train_id,stop_seq,station_id,departure_time,distance_km) VALUES (%s,1,%s,%s,0)', [train,sample_stations['source_id'],departure.time()])
        c.execute('INSERT INTO train_stop(train_id,stop_seq,station_id,arrival_time,distance_km) VALUES (%s,2,%s,%s,100)', [train,sample_stations['dest_id'],departure.time()])
        c.execute("INSERT INTO coach(train_id,class_code,coach_number) VALUES (%s,'3A','B1')", [train])
        coach = c.lastrowid
        c.execute("INSERT INTO seat(coach_id,seat_number,berth_type) VALUES (%s,1,'LB'),(%s,2,'UB')", [coach,coach])
        c.execute('INSERT INTO train_run(train_id,journey_date) VALUES (%s,%s)', [train,departure.date()])
        run = c.lastrowid
        c.execute('CALL sp_generate_run_inventory(%s)', [run])
    booking = hold(api_client, customer_auth_headers, run, sample_stations)
    assert pay(api_client, customer_auth_headers, booking['pnr']).status_code == 200
    result = api_client.post(f"/api/bookings/{booking['pnr']}/cancel/", {'reason':'Refund tier test'}, format='json', **customer_auth_headers)
    assert result.status_code == 200, result.data
    assert Decimal(str(result.data['cancellation']['refund_amount'])) == (Decimal(str(booking['total_fare']))*Decimal(ratio)).quantize(Decimal('0.01'))


@pytest.mark.django_db(transaction=True, databases=['default','readonly'])
def test_concurrent_same_key_payment(api_client, customer_auth_headers, sample_run_id, sample_stations):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    booking = hold(api_client, customer_auth_headers, sample_run_id, sample_stations)
    key = str(uuid.uuid4())
    barrier = threading.Barrier(2)
    def worker(index):
        conn = connections['default'].copy()
        try:
            barrier.wait(timeout=10)
            with conn.cursor() as c:
                c.execute("CALL sp_confirm_payment(%s,%s,'UPI',%s,%s,@s,@m)", [booking['pnr'],booking['total_fare'],f'TXN-{uuid.uuid4().hex}',key])
                c.execute('SELECT @s')
                return c.fetchone()[0]
        finally:
            conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(worker, range(2))) == ['SUCCESS','SUCCESS']
    with connections['readonly'].cursor() as c:
        c.execute('SELECT COUNT(*) FROM payment WHERE pnr=%s', [booking['pnr']])
        assert c.fetchone()[0] == 1
