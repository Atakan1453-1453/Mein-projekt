import type { Page } from '@playwright/test';

/** Alle öffentlichen Seiten (für Seiten-, A11y- und SEO-Tests). */
export const PAGES = [
  { path: '/', name: 'Startseite' },
  { path: '/ueber-uns/', name: 'Über uns' },
  { path: '/shops/', name: 'Shops & Services' },
  { path: '/galerie/', name: 'Galerie' },
  { path: '/kontakt/', name: 'Kontakt' },
  { path: '/impressum/', name: 'Impressum' },
  { path: '/datenschutz/', name: 'Datenschutz' },
] as const;

/** Status- und Fehlerseiten (noindex). */
export const NOINDEX_PAGES = ['/kontakt/danke/', '/kontakt/fehler/'] as const;

/**
 * Sammelt Konsolenfehler, JavaScript-Fehler, fehlgeschlagene Requests und
 * HTTP-Fehler (≥ 400) – darunter auch Verstöße gegen die Content-Security-Policy.
 */
export function collectProblems(page: Page): string[] {
  const problems: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') problems.push(`console: ${msg.text()}`);
  });
  page.on('pageerror', (err) => problems.push(`pageerror: ${err.message}`));
  page.on('requestfailed', (req) => problems.push(`requestfailed: ${req.url()} (${req.failure()?.errorText})`));
  page.on('response', (res) => {
    if (res.status() >= 400) problems.push(`HTTP ${res.status()}: ${res.url()}`);
  });
  return problems;
}
