/**
 * Galerie-Großansicht: Tastaturbedienung, Blättern, Fokus-Rückgabe.
 */
import { test, expect } from '@playwright/test';

test('Großansicht per Tastatur öffnen, blättern und schließen', async ({ page }) => {
  await page.goto('/galerie/');
  const first = page.locator('[data-gallery-index="0"]');
  await first.focus();
  await page.keyboard.press('Enter');

  const dialog = page.getByRole('dialog', { name: 'Bild-Großansicht' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Großansicht schließen' })).toBeFocused();
  await expect(dialog.locator('[data-lightbox-counter]')).toHaveText('1 / 9');

  await page.keyboard.press('ArrowRight');
  await expect(dialog.locator('[data-lightbox-counter]')).toHaveText('2 / 9');
  await expect(dialog.locator('[data-lightbox-caption]')).toHaveText('Haupteingang');

  await page.keyboard.press('ArrowLeft');
  await page.keyboard.press('ArrowLeft');
  await expect(dialog.locator('[data-lightbox-counter]')).toHaveText('9 / 9');

  // Großes Bild wird tatsächlich geladen
  const loaded = await dialog.locator('img').evaluate(async (img: HTMLImageElement) => {
    if (!img.complete) await new Promise((r) => img.addEventListener('load', r, { once: true }));
    return img.naturalWidth;
  });
  expect(loaded).toBeGreaterThan(1000);

  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(first).toBeFocused();
});

test('ohne JavaScript verlinken die Vorschaubilder auf die große Bilddatei', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL: 'http://127.0.0.1:4322' });
  const page = await context.newPage();
  await page.goto('/galerie/');
  const href = await page.locator('[data-gallery-index="0"]').getAttribute('href');
  expect(href).toMatch(/^\/_astro\/.+\.webp$/);
  const res = await page.request.get(href!);
  expect(res.status()).toBe(200);
  expect(res.headers()['content-type']).toBe('image/webp');
  await context.close();
});

test('Bilder werden in modernen Formaten mit mehreren Größen ausgeliefert', async ({ page }) => {
  await page.goto('/galerie/');
  const picture = page.locator('.gallery__item picture').first();
  await expect(picture.locator('source[type="image/avif"]')).toHaveCount(1);
  await expect(picture.locator('source[type="image/webp"]')).toHaveCount(1);
  const srcset = await picture.locator('source[type="image/avif"]').getAttribute('srcset');
  expect(srcset?.split(',').length).toBeGreaterThanOrEqual(3);
  const img = picture.locator('img');
  await expect(img).toHaveAttribute('width', /\d+/);
  await expect(img).toHaveAttribute('height', /\d+/);
});
