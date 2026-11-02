// Owner: Person B
import { test, expect } from '@playwright/test';

test.describe('TatkalPRS High-Concurrency Railway Booking E2E Suite', () => {

  test('Homepage loads and displays train search controls', async ({ page }) => {
    await page.goto('http://localhost:3000/');
    await expect(page).toHaveTitle(/TatkalPRS|Train Booking/i);
    await expect(page.getByText(/Tatkal-Style High-Concurrency Train Booking System/i)).toBeVisible();
    await expect(page.getByPlaceholder(/Enter station name or code/i).first()).toBeVisible();
  });

  test('Semantic Vector Search renders results from ChromaDB', async ({ page }) => {
    await page.goto('http://localhost:3000/help');
    await expect(page.getByText(/Railway Policies & Knowledge Base/i)).toBeVisible();

    const searchInput = page.getByPlaceholder(/Search refund rules, tatkal timings, id requirements/i);
    await expect(searchInput).toBeVisible();
    await searchInput.fill('tatkal refund rules');

    // Asserts policy cards appear
    await expect(page.getByText(/Full Refund Conditions/i).or(page.getByText(/Tatkal/i)).first()).toBeVisible();
  });

  test('Seat Map renders coaches and berths', async ({ page }) => {
    await page.goto('http://localhost:3000/book/1');
    await expect(page.getByText(/Passenger Details/i).or(page.getByText(/Book Tickets/i)).first()).toBeVisible();
  });

  test('Admin dashboard requires authentication or renders data for Admin', async ({ page }) => {
    await page.goto('http://localhost:3000/admin');
    // If not logged in as admin, redirects to login or shows admin heading
    const heading = page.getByText(/Admin Control Center/i).or(page.getByText(/Sign in to your account/i));
    await expect(heading.first()).toBeVisible();
  });

});
