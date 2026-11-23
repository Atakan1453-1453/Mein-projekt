/**
 * Navigation & Tastaturbedienung.
 */
import { test, expect } from '@playwright/test';
import { PAGES } from './helpers';

test('„Zum Inhalt springen“ ist der erste Tab-Stopp und springt zum Hauptinhalt', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  const skip = page.getByRole('link', { name: 'Zum Inhalt springen' });
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page.locator('main#inhalt')).toBeFocused();
});

test('alle Menüpunkte führen zur richtigen Seite und markieren sie als aktuell', async ({ page }, testInfo) => {
  const isMobile = (testInfo.project.use.viewport?.width ?? 1280) < 1024;
  for (const { path, name } of PAGES.filter((p) => !['/impressum/', '/datenschutz/'].includes(p.path))) {
    await page.goto('/');
    if (isMobile) await page.getByRole('button', { name: 'Menü' }).click();
    const nav = page.getByRole('navigation', { name: 'Hauptnavigation' });
    const label = name === 'Startseite' ? 'Start' : name;
    await nav.getByRole('link', { name: label, exact: true }).click();
    await expect(page).toHaveURL(path);
    if (isMobile) await page.getByRole('button', { name: 'Menü' }).click();
    await expect(nav.getByRole('link', { name: label, exact: true })).toHaveAttribute('aria-current', 'page');
  }
});

test('mobiles Menü: auf-/zuklappen, Escape schließt und gibt Fokus zurück', async ({ page }, testInfo) => {
  test.skip((testInfo.project.use.viewport?.width ?? 1280) >= 1024, 'Nur bei schmalen Bildschirmen');
  await page.goto('/');
  const toggle = page.getByRole('button', { name: 'Menü' });
  const navLink = page.getByRole('navigation', { name: 'Hauptnavigation' }).getByRole('link', { name: 'Galerie' });

  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expect(navLink).toBeHidden();

  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await expect(navLink).toBeVisible();

  await navLink.focus();
  await page.keyboard.press('Escape');
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expect(toggle).toBeFocused();
  await expect(navLink).toBeHidden();
});

test('Navigation ist auch ohne JavaScript vollständig erreichbar', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 740 } });
  const page = await context.newPage();
  await page.goto('/');
  for (const label of ['Über uns', 'Shops & Services', 'Galerie', 'Kontakt']) {
    await expect(page.getByRole('navigation', { name: 'Hauptnavigation' }).getByRole('link', { name: label })).toBeVisible();
  }
  await context.close();
});

test('Footer verlinkt Impressum und Datenschutz auf jeder Seite', async ({ page }) => {
  for (const { path } of PAGES) {
    await page.goto(path);
    const footer = page.locator('footer');
    await expect(footer.getByRole('link', { name: 'Impressum' })).toHaveAttribute('href', '/impressum/');
    await expect(footer.getByRole('link', { name: 'Datenschutz' })).toHaveAttribute('href', '/datenschutz/');
  }
});

test('Fokus ist bei Tastaturbedienung immer sichtbar', async ({ page }) => {
  await page.goto('/');
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab');
    const outline = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || el === document.body) return 'body';
      const s = getComputedStyle(el);
      return `${s.outlineStyle} ${s.outlineWidth}`;
    });
    if (outline === 'body') continue;
    expect(outline, `Element ${i + 1} ohne Fokusrahmen`).not.toMatch(/^none|0px$/);
  }
});
