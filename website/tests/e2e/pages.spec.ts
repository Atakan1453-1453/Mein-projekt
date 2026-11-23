/**
 * Für JEDE Seite in JEDER Bildschirmbreite:
 *  - lädt ohne Fehler (keine Konsolen-/CSP-Fehler, keine kaputten Ressourcen)
 *  - kein horizontales Scrollen
 *  - genau eine H1, Bilder mit Alternativtext
 *  - keine Barrierefreiheits-Verstöße laut axe-core (WCAG 2.2 AA)
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { PAGES, NOINDEX_PAGES, collectProblems } from './helpers';

for (const { path, name } of [...PAGES, ...NOINDEX_PAGES.map((p) => ({ path: p, name: p }))]) {
  test.describe(`${name} (${path})`, () => {
    test('lädt fehlerfrei und ohne horizontales Scrollen', async ({ page }) => {
      const problems = collectProblems(page);
      const response = await page.goto(path, { waitUntil: 'networkidle' });
      expect(response?.status()).toBe(200);

      // Alle Bilder (auch lazy) einmal laden lassen
      await page.evaluate(async () => {
        for (let y = 0; y < document.body.scrollHeight; y += window.innerHeight) {
          window.scrollTo(0, y);
          await new Promise((r) => setTimeout(r, 30));
        }
        window.scrollTo(0, 0);
      });
      await page.waitForLoadState('networkidle');

      expect(problems, problems.join('\n')).toEqual([]);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow, 'Seite ist breiter als der Bildschirm').toBeLessThanOrEqual(0);

      await expect(page.locator('h1')).toHaveCount(1);
      await expect(page.locator('img:not([alt])')).toHaveCount(0);
      await expect(page.locator('html')).toHaveAttribute('lang', 'de');
    });

    test('ist barrierefrei (axe, WCAG 2.2 AA)', async ({ page }) => {
      await page.goto(path, { waitUntil: 'networkidle' });
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'])
        .analyze();
      const summary = results.violations.map(
        (v) => `${v.id} (${v.impact}): ${v.help}\n   ${v.nodes.map((n) => n.target.join(' ')).join('\n   ')}`,
      );
      expect(summary, summary.join('\n')).toEqual([]);
    });
  });
}

test('404-Seite liefert Status 404 und hilfreiche Links', async ({ page }) => {
  const response = await page.goto('/diese-seite-gibt-es-nicht/');
  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1 })).toContainText('gibt es leider nicht');
  await expect(page.locator('main a[href="/kontakt/"]')).toBeVisible();
});
