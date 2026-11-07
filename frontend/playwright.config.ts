// Owner: Person B
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['html', {open: 'never'}]],
  timeout: 150000,
  webServer: [
    {command: process.platform === 'win32' ? '..\\.venv\\Scripts\\python.exe ..\\backend\\manage.py runserver 127.0.0.1:8100 --noreload' : '../.venv/bin/python ../backend/manage.py runserver 127.0.0.1:8100 --noreload', url: 'http://127.0.0.1:8100/api/trains/', env: {CORS_ALLOWED_ORIGINS: 'http://127.0.0.1:3100'}, timeout: 120000, reuseExistingServer: false},
    {command: 'npm run build && node node_modules/next/dist/bin/next start -p 3100', env: {NEXT_PUBLIC_API_URL: 'http://127.0.0.1:8100/api', NEXT_BUILD_DIR: '.next-e2e'}, url: 'http://127.0.0.1:3100', timeout: 240000, reuseExistingServer: false},
  ],
  use: {
    actionTimeout: 15000,
    baseURL: 'http://127.0.0.1:3100',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
