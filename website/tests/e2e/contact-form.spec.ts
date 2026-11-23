/**
 * Kontaktformular: Browser-Validierung, Versand, Spam-Schutz, Fallback ohne
 * JavaScript und serverseitige Prüfung bei umgangener Browser-Validierung.
 * Versendete Mails landen im Test als .eml-Datei in .tmp/test-storage/mails.
 */
import { test, expect, type Page } from '@playwright/test';
import { readdir, readFile } from 'node:fs/promises';

const MAIL_DIR = '.tmp/test-storage/mails';

// Formular-Tests laufen einmal (Desktop) – das Layout wird in pages.spec.ts geprüft.
test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1280', 'Formularlogik nur einmal testen');
});

async function mailsContaining(text: string): Promise<string[]> {
  const files = await readdir(MAIL_DIR).catch(() => [] as string[]);
  const contents = await Promise.all(files.map((f) => readFile(`${MAIL_DIR}/${f}`, 'utf8')));
  return contents.filter((c) => c.includes(text));
}

async function fillValid(page: Page, marker: string) {
  await page.getByLabel('Ihr Anliegen').selectOption('allgemein');
  await page.getByLabel('Name', { exact: false }).first().fill('Erika Test');
  await page.getByLabel('E-Mail-Adresse').fill('erika@example.org');
  await page.getByLabel('Ihre Nachricht').fill(`Hallo, dies ist eine automatisierte Testnachricht. ${marker}`);
}

test('zeigt verständliche Fehlermeldungen und eine Fehlerübersicht', async ({ page }) => {
  await page.goto('/kontakt/');
  await page.getByRole('button', { name: 'Anfrage senden' }).click();

  const summary = page.getByRole('alert');
  await expect(summary).toBeVisible();
  await expect(summary).toBeFocused();
  await expect(summary).toContainText('Bitte wählen Sie Ihr Anliegen aus.');
  await expect(summary).toContainText('Bitte geben Sie Ihren Namen ein.');
  await expect(page.locator('#email')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.locator('#email-error')).toHaveText('Bitte geben Sie Ihre E-Mail-Adresse ein.');

  // Link in der Übersicht springt zum Feld
  await summary.getByRole('link', { name: 'Bitte geben Sie Ihren Namen ein.' }).click();
  await expect(page.locator('#name')).toBeFocused();

  // Ungültige E-Mail und zu kurze Nachricht
  await page.locator('#email').fill('keine-mail');
  await page.locator('#nachricht').fill('zu kurz');
  await page.getByRole('button', { name: 'Anfrage senden' }).click();
  await expect(page.locator('#email-error')).toContainText('gültige E-Mail-Adresse');
  await expect(page.locator('#nachricht-error')).toContainText('mindestens 20 Zeichen');
});

test('sendet eine gültige Anfrage und leitet zur Danke-Seite weiter', async ({ page }) => {
  const marker = `E2E-${Date.now()}`;
  await page.goto('/kontakt/');
  await fillValid(page, marker);
  await expect(page.locator('[data-form-token]')).not.toHaveValue('');
  await page.waitForTimeout(3200); // Mindest-Ausfüllzeit des Spam-Schutzes
  await page.getByRole('button', { name: 'Anfrage senden' }).click();
  await expect(page).toHaveURL('/kontakt/danke/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Vielen Dank für Ihre Anfrage!');

  const mails = await mailsContaining(marker);
  expect(mails).toHaveLength(1);
  expect(mails[0]).toContain('Reply-To: Erika Test <erika@example.org>');
  expect(mails[0]).toContain('Allgemeine Anfrage');
});

test('Vorauswahl „Vermietung“ per URL blendet die Zusatzfelder ein', async ({ page }) => {
  const marker = `E2E-MIETE-${Date.now()}`;
  await page.goto('/kontakt/?anliegen=vermietung#formular');
  await expect(page.getByLabel('Ihr Anliegen')).toHaveValue('vermietung');
  await expect(page.getByLabel('Flächenbedarf (ca. m²)')).toBeVisible();

  await page.getByLabel('Name', { exact: false }).first().fill('Max Mieter');
  await page.getByLabel('E-Mail-Adresse').fill('max@example.org');
  await page.getByLabel('Branche / Sortiment').fill('Feinkost');
  await page.getByLabel('Flächenbedarf (ca. m²)').fill('80');
  await page.getByLabel('Ihre Nachricht').fill(`Wir suchen eine Fläche für ein Feinkostgeschäft. ${marker}`);
  await page.waitForTimeout(3200);
  await page.getByRole('button', { name: 'Anfrage senden' }).click();
  await expect(page).toHaveURL('/kontakt/danke/');

  const mails = await mailsContaining(marker);
  expect(mails).toHaveLength(1);
  expect(mails[0]).toContain('Angaben zur Mietanfrage');
  expect(mails[0]).toContain('Feinkost');

  // Bei anderem Anliegen sind die Zusatzfelder ausgeblendet
  await page.goto('/kontakt/');
  await page.getByLabel('Ihr Anliegen').selectOption('presse');
  await expect(page.getByLabel('Flächenbedarf (ca. m²)')).toBeHidden();
});

test('Spam-Schutz: zu schnelles Absenden wird abgelehnt, nichts wird gesendet', async ({ page }) => {
  const marker = `E2E-FAST-${Date.now()}`;
  await page.goto('/kontakt/');
  await fillValid(page, marker);
  await expect(page.locator('[data-form-token]')).not.toHaveValue('');
  await page.getByRole('button', { name: 'Anfrage senden' }).click();
  await expect(page.getByRole('alert')).toContainText('Das ging sehr schnell');
  expect(await mailsContaining(marker)).toHaveLength(0);
});

test('Spam-Schutz: ausgefülltes Honeypot-Feld → scheinbarer Erfolg, aber keine Mail', async ({ page }) => {
  const marker = `E2E-BOT-${Date.now()}`;
  await page.goto('/kontakt/');
  await fillValid(page, marker);
  await page.locator('#website').fill('https://spam.example', { force: true });
  await page.waitForTimeout(3200);
  await page.getByRole('button', { name: 'Anfrage senden' }).click();
  await expect(page).toHaveURL('/kontakt/danke/');
  expect(await mailsContaining(marker)).toHaveLength(0);
});

test('funktioniert ohne JavaScript (klassischer POST + Weiterleitung)', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL: 'http://127.0.0.1:4322' });
  const page = await context.newPage();
  const marker = `E2E-NOJS-${Date.now()}`;
  await page.goto('/kontakt/');
  await expect(page.getByLabel('Flächenbedarf (ca. m²)')).toBeVisible(); // ohne JS immer sichtbar
  await fillValid(page, marker);
  await page.getByRole('button', { name: 'Anfrage senden' }).click();
  await expect(page).toHaveURL('/kontakt/danke/');
  expect(await mailsContaining(marker)).toHaveLength(1);
  await context.close();
});

test('Server prüft selbst, auch wenn die Browser-Prüfung umgangen wird', async ({ request }) => {
  const res = await request.post('/api/kontakt.php', {
    headers: { Accept: 'application/json', Origin: 'http://127.0.0.1:4322' },
    form: { anliegen: 'gibtsnicht', name: 'X', email: "a@b.de\r\nBcc: opfer@example.com", nachricht: 'kurz' },
  });
  expect(res.status()).toBe(422);
  const body = await res.json();
  expect(Object.keys(body.errors).sort()).toEqual(['anliegen', 'email', 'nachricht', 'name']);
});

test('Server lehnt Absendungen von fremden Websites ab', async ({ request }) => {
  const res = await request.post('/api/kontakt.php', {
    headers: { Accept: 'application/json', Origin: 'https://boese-seite.example' },
    form: { anliegen: 'allgemein', name: 'Erika Test', email: 'erika@example.org', nachricht: 'Eine ausreichend lange Testnachricht.' },
  });
  expect(res.status()).toBe(403);
});

test('interne Dateien des Formular-Handlers sind nicht abrufbar', async ({ request }) => {
  for (const path of ['/api/lib/form-config.json', '/api/lib/bootstrap.php', '/api/lib/src/Config.php', '/.htaccess']) {
    const res = await request.get(path);
    expect(res.status(), path).toBe(403);
  }
  const get = await request.get('/api/kontakt.php');
  expect(get.status()).toBe(405);
});
