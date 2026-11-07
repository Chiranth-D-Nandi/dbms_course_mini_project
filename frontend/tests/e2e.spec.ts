import { test, expect, Page } from '@playwright/test';

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8100/api';
const journeyDate = () => {const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().slice(0,10);};

async function login(page: Page, admin = false) {
  await page.goto('/login');
  await page.locator('input[type=email]').fill(admin ? 'admin@tatkal.com' : 'chiranth@example.com');
  await page.locator('input[type=password]').fill(admin ? 'Admin@123' : 'Customer@123');
  await page.getByRole('button', {name: 'Sign In', exact: true}).click();
  await expect(page).toHaveURL(admin ? /\/admin$/ : /\/search$/);
}

test('customer searches, reserves two seats, pays, views and cancels a ticket', async ({page, request}) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await login(page);
  const stations = await (await request.get(`${API}/stations/`)).json();
  const from = stations.find((s: any) => s.station_code === 'SBC').station_id;
  const to = stations.find((s: any) => s.station_code === 'MAS').station_id;
  await page.goto(`/search?from=${from}&to=${to}&date=${journeyDate()}&class=3A`);
  await expect(page.getByRole('link', {name: 'Book General', exact: true}).first()).toBeVisible();
  await page.getByRole('link', {name: 'View Halt Schedule'}).first().click();
  await expect(page).toHaveURL(/\/trains\/\d+$/);
  await expect(page.getByText('Runs:', {exact: false})).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\/search\?/);
  await page.getByRole('link', {name: 'Book General', exact: true}).first().click();
  await expect(page.getByRole('heading', {name: 'Book tickets', exact: true})).toBeVisible();
  await page.getByLabel('Passenger 1 name').fill('Browser Test Passenger');
  await page.getByLabel('Passenger 1 date of birth').fill('1995-05-15');
  await page.getByLabel('Passenger 1 ID number').fill('123456789012');
  await page.getByRole('button', {name: 'Add passenger'}).click();
  await page.getByLabel('Passenger 2 name').fill('Browser Second Passenger');
  await page.getByLabel('Passenger 2 date of birth').fill('1997-04-20');
  await page.getByLabel('Passenger 2 ID number').fill('123456789013');
  await page.getByRole('button', {name: 'Reserve seats for 8 minutes'}).click();
  await expect(page).toHaveURL(/\/pay\/\d+$/);
  await expect(page.getByRole('timer')).toContainText('remaining');
  await page.getByRole('button', {name: /Confirm & pay/}).click();
  await expect(page).toHaveURL(/\/bookings\/\d+$/);
  await expect(page.getByRole('status')).toHaveText('CONFIRMED');
  await expect(page.getByText('Browser Second Passenger', {exact: true})).toBeVisible();
  await page.screenshot({path: 'test-results/ticket-confirmed.png', fullPage: true});
  await page.getByLabel('Reason').fill('Browser regression test');
  await page.getByRole('button', {name: 'Cancel confirmed ticket'}).click();
  await expect(page.getByRole('status')).toHaveText('CANCELLED');
  await expect(page.getByText(/Cancelled · Refund:/)).toBeVisible();
  await page.getByRole('link', {name: /View all my bookings/}).click();
  await expect(page.getByText('CANCELLED', {exact: true}).first()).toBeVisible();
  expect(errors).toEqual([]);
});

test('homepage autocomplete and train number lookup use the real catalog', async ({page}) => {
  await page.goto('/');
  await page.getByPlaceholder('e.g. SBC, Bengaluru City').fill('SBC');
  await page.getByRole('button').filter({hasText: 'KSR Bengaluru City'}).click();
  await page.getByPlaceholder('e.g. MAS, Chennai Central').fill('MAS');
  await page.getByRole('button').filter({hasText: 'Puratchi Thalaivar'}).click();
  await page.locator('input[type=date]').fill(journeyDate());
  await page.getByRole('button', {name: /Search Trains & Seat Availability/}).click();
  await expect(page.getByRole('link', {name: 'Book General', exact: true}).first()).toBeVisible();
  await page.goto('/');
  await page.getByRole('button', {name: 'Train Timetable', exact: true}).click();
  await page.getByPlaceholder(/Enter Train Number/).fill('12658');
  await page.getByRole('button', {name: 'View Timetable', exact: true}).click();
  await expect(page).toHaveURL(/\/trains\/\d+$/);
  await expect(page.getByText('Runs:', {exact: false})).toBeVisible();
});

test('semantic FAQ and train discovery return live results', async ({page}) => {
  await page.goto('/help');
  await page.getByPlaceholder(/Can I get a refund/).fill('tatkal cancellation refund');
  await page.getByRole('button', {name: 'Search Knowledge Base'}).click();
  await expect(page.getByText(/Semantic Vector Matches/)).toBeVisible({timeout: 120000});
  await expect(page.getByText(/% match/).first()).toBeVisible();
  await page.goto('/');
  await page.getByPlaceholder(/Fast overnight superfast express/).fill('fast morning train Bangalore Chennai');
  await page.getByRole('button', {name: 'Find Best Match'}).click();
  await expect(page.getByText('Top Semantic Matches:')).toBeVisible({timeout: 120000});
  await page.getByText('Top Semantic Matches:').locator('..').getByText(/#\d+/).first().click();
  await expect(page).toHaveURL(/\/trains\/\d+$/);
  await expect(page.getByText('Runs:', {exact: false})).toBeVisible();
});

test('admin sees real reports and audits, schedules inventory and runs expiry sweep', async ({page}) => {
  await login(page, true);
  await expect(page.getByRole('heading', {name: /Admin Control Center/})).toBeVisible();
  await expect(page.locator('tbody tr').first()).toBeVisible();
  await page.getByRole('link', {name: /Audit Trail/}).click();
  await expect(page.locator('tbody').getByText('booking', {exact: true}).first()).toBeVisible();
  await page.goto('/admin/runs');
  await page.getByPlaceholder('e.g. 101').fill('1');
  const date = new Date(); date.setDate(date.getDate()+40+Math.floor(Math.random()*1000));
  await page.getByLabel('Journey date').fill(date.toISOString().slice(0,10));
  await page.getByRole('button', {name: 'Create run and inventory'}).click();
  await expect(page.getByText(/Run created successfully/)).toBeVisible();
  await page.getByRole('button', {name: 'Release expired holds now'}).click();
  await expect(page.getByText(/Hold sweep completed/)).toBeVisible();
  await page.goto('/admin/trains');
  await expect(page.getByRole('link', {name: /View Timetable/}).first()).toBeVisible();
  await page.screenshot({path: 'test-results/admin-catalog.png', fullPage: true});
});

test('mobile navigation and unauthenticated booking access work', async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await page.goto('/');
  await expect(page.getByRole('button', {name: /Search Trains & Seat Availability/})).toBeVisible();
  await page.screenshot({path: 'test-results/mobile-home.png', fullPage: true});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.goto('/book/1?class=3A&type=GENERAL&src=1&dst=2');
  await expect(page).toHaveURL(/\/login\?next=/);
});
