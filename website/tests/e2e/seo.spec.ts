/**
 * Technische SEO-Grundlagen und Sicherheits-Header.
 */
import { test, expect } from '@playwright/test';
import { PAGES, NOINDEX_PAGES } from './helpers';
import { DEMO_MODE } from '../../src/config/site';

const SITE = 'https://galeriekoenigshof.de';

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1280', 'Unabhängig von der Bildschirmbreite – einmal genügt');
});

test('jede Seite hat eigenen Titel, Beschreibung, Canonical und Open-Graph-Daten', async ({ page }) => {
  const titles = new Set<string>();
  const descriptions = new Set<string>();

  for (const { path } of PAGES) {
    await page.goto(path);
    const title = await page.title();
    const description = await page.locator('meta[name="description"]').getAttribute('content');

    expect(title.length, `${path}: Titel-Länge`).toBeGreaterThan(10);
    expect(title.length, `${path}: Titel-Länge`).toBeLessThanOrEqual(65);
    expect(description?.length ?? 0, `${path}: Beschreibung zu kurz`).toBeGreaterThanOrEqual(70);
    expect(description?.length ?? 0, `${path}: Beschreibung zu lang`).toBeLessThanOrEqual(170);
    titles.add(title);
    descriptions.add(description ?? '');

    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', SITE + path);
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute('content', `${SITE}/og-image.png`);
    // Testversion: alle Seiten noindex; live: kein robots-Meta-Tag
    if (DEMO_MODE) await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
    else await expect(page.locator('meta[name="robots"]')).toHaveCount(0);
  }

  expect(titles.size, 'Titel müssen eindeutig sein').toBe(PAGES.length);
  expect(descriptions.size, 'Beschreibungen müssen eindeutig sein').toBe(PAGES.length);
});

test('Status-Seiten sind auf noindex gesetzt', async ({ page }) => {
  for (const path of NOINDEX_PAGES) {
    await page.goto(path);
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, follow');
    await expect(page.locator('link[rel="canonical"]')).toHaveCount(0);
  }
});

test('Überschriften-Hierarchie überspringt keine Ebene', async ({ page }) => {
  for (const { path } of PAGES) {
    await page.goto(path);
    const levels = await page.locator('main :is(h1,h2,h3,h4)').evaluateAll((els) => els.map((e) => Number(e.tagName[1])));
    expect(levels[0], `${path}: erste Überschrift muss H1 sein`).toBe(1);
    for (let i = 1; i < levels.length; i++) {
      expect(levels[i]! - levels[i - 1]!, `${path}: Sprung von H${levels[i - 1]} auf H${levels[i]}`).toBeLessThanOrEqual(1);
    }
  }
});

test('robots.txt und Sitemap sind korrekt', async ({ request }) => {
  const robots = await (await request.get('/robots.txt')).text();
  expect(robots).toContain(`Sitemap: ${SITE}/sitemap-index.xml`);
  expect(robots).toMatch(DEMO_MODE ? /^Disallow: \/$/m : /^Disallow: \/api\/$/m);

  const sitemap = await (await request.get('/sitemap-0.xml')).text();
  for (const { path } of PAGES) expect(sitemap).toContain(`<loc>${SITE}${path}</loc>`);
  for (const path of NOINDEX_PAGES) expect(sitemap).not.toContain(path);
  expect(sitemap).not.toContain('404');
});

test('Testversion ist als solche gekennzeichnet', async ({ page }) => {
  test.skip(!DEMO_MODE, 'nur in der Testversion');
  for (const { path } of PAGES) {
    await page.goto(path);
    await expect(page.getByRole('complementary', { name: 'Hinweis zur Testversion' })).toContainText('fiktive Beispiele');
  }
});

test('strukturierte Daten (JSON-LD) auf der Startseite sind gültiges JSON mit Adresse und Öffnungszeiten', async ({ page }) => {
  await page.goto('/');
  const raw = await page.locator('script[type="application/ld+json"]').textContent();
  const data = JSON.parse(raw ?? '{}');
  expect(data['@type']).toBe('ShoppingCenter');
  expect(data.address.streetAddress).toBe('Talstraße 10');
  expect(data.address.postalCode).toBe('40822');
  expect(data.openingHoursSpecification[0].opens).toBe('10:00');
  // Fiktive Testwerte dürfen nie in strukturierte Daten gelangen
  expect(raw).not.toContain('example.com');
  expect(raw).not.toContain('0000000');
});

test('Sicherheits-Header werden gesendet', async ({ request }) => {
  const res = await request.get('/');
  const h = res.headers();
  expect(h['content-security-policy']).toContain("default-src 'self'");
  expect(h['content-security-policy']).toContain("frame-ancestors 'none'");
  expect(h['x-content-type-options']).toBe('nosniff');
  expect(h['referrer-policy']).toBe('strict-origin-when-cross-origin');
  expect(h['x-frame-options']).toBe('DENY');
  expect(h['permissions-policy']).toContain('camera=()');
  expect(h['x-powered-by']).toBeUndefined();
});

test('keine Cookies, keine Drittanbieter-Anfragen', async ({ page, context }) => {
  const external: string[] = [];
  page.on('request', (req) => {
    const url = new URL(req.url());
    if (url.hostname !== '127.0.0.1') external.push(req.url());
  });
  for (const { path } of PAGES) await page.goto(path, { waitUntil: 'networkidle' });
  expect(external).toEqual([]);
  expect(await context.cookies()).toEqual([]);
  const storage = await page.evaluate(() => localStorage.length + sessionStorage.length);
  expect(storage).toBe(0);
});
