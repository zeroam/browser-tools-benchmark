import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './demo',
  workers: 1,
  retries: 0,
  timeout: 15000,
  expect: { timeout: 4000 },
  outputDir: '../.demo/test-results',
  reporter: 'list',
  use: {
    baseURL: process.env.DEMO_URL || 'http://demo.localhost:5420',
    channel: process.env.PW_CHANNEL === 'chromium' ? undefined : (process.env.PW_CHANNEL || 'chrome'),
    headless: true,
    trace: 'retain-on-failure',
  },
});
