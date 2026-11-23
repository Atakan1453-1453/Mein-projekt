/**
 * End-to-End-Tests im echten Browser (Chromium) gegen den gebauten Stand
 * (dist/) – ausgeliefert über PHP mit denselben Sicherheits-Headern wie live.
 *
 *   npm run build && npm run test:e2e
 *
 * Getestete Bildschirmbreiten: 360 (Smartphone), 768 (Tablet),
 * 1280 (Laptop), 1920 (großer Monitor).
 */
import { defineConfig, devices } from '@playwright/test';

const PORT = 4322;

export default defineConfig({
  testDir: './tests/e2e',
  globalSetup: './tests/e2e/global-setup.ts',
  fullyParallel: true,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 1 : 0,
  reporter: process.env['CI'] ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    reducedMotion: 'reduce',
    locale: 'de-DE',
    trace: 'off',
  },
  projects: [
    { name: 'mobil-360', use: { ...devices['Desktop Chrome'], viewport: { width: 360, height: 740 }, isMobile: false, hasTouch: true } },
    { name: 'tablet-768', use: { ...devices['Desktop Chrome'], viewport: { width: 768, height: 1024 } } },
    { name: 'desktop-1280', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } } },
    { name: 'wide-1920', use: { ...devices['Desktop Chrome'], viewport: { width: 1920, height: 1080 } } },
  ],
  webServer: {
    command: `php -S 127.0.0.1:${PORT} -t dist scripts/php-router.php`,
    url: `http://127.0.0.1:${PORT}/`,
    reuseExistingServer: !process.env['CI'],
    env: { KONTAKT_CONFIG: 'tests/fixtures/kontakt-config.test.php' },
    stdout: 'ignore',
    stderr: 'ignore',
  },
});
