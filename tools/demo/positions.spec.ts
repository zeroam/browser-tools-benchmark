import { test, expect } from '@playwright/test';

// Expected values are independent of the app response. Keep every cell and row count.
const expected = [
  ['BTCUSDT', 'LONG', '0.120', '61250.5'],
  ['ETHUSDT', 'SHORT', '1.500', '2410.2'],
  ['SOLUSDT', 'LONG', '30.00', '142.35'],
  ['XRPUSDT', 'LONG', '2500', '0.5821'],
  ['ADAUSDT', 'SHORT', '4000', '0.3375'],
];

test('bot list opens the correct detail and all positions match', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'alpha-trend', exact: true }).click();
  await expect(page.locator('#title'), 'BOT_DETAIL: clicked bot must open').toHaveText('alpha-trend');
  const rows = page.locator('#positions tbody tr');
  await expect(rows, 'POSITION_ROWS: exact row count').toHaveCount(expected.length);
  for (let i = 0; i < expected.length; i++) {
    await expect(rows.nth(i).locator('td'), `POSITION_ROWS: row ${i + 1} every cell`).toHaveText(expected[i]);
  }
});
