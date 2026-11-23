// @ts-check
/**
 * Astro-Konfiguration der Website „Galerie Königshof Mettmann“.
 *
 * Wichtig für den Livegang:
 *  - SITE_URL muss auf die echte, kanonische Domain zeigen (inkl. https:// und
 *    ohne abschließenden Slash). Sie wird für Canonical-Links, Sitemap,
 *    robots.txt, Open-Graph-Bilder und strukturierte Daten verwendet.
 *    Setzen per Umgebungsvariable:  SITE_URL=https://www.example.de npm run build
 */
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const SITE_URL = process.env.SITE_URL ?? 'https://galeriekoenigshof.de';

/** Seiten, die nicht in die Sitemap gehören (Status-Seiten des Formulars). */
const NOINDEX_PATHS = ['/kontakt/danke/', '/kontakt/fehler/', '/404/'];

export default defineConfig({
  site: SITE_URL,
  // Alle URLs enden auf „/“ – passt zur Verzeichnisstruktur im Build
  // (ueber-uns/index.html) und verhindert doppelte Inhalte.
  trailingSlash: 'always',
  build: {
    format: 'directory',
    // Keine Inline-<style>-Blöcke: ermöglicht eine strenge Content-Security-Policy
    // ohne 'unsafe-inline' (siehe config/security-headers.json).
    inlineStylesheets: 'never',
  },
  vite: {
    build: {
      // Keine Inline-Skripte/Data-URIs: alles als eigene, gecachte Datei.
      assetsInlineLimit: 0,
    },
  },
  // Keine Telemetrie-/Prefetch-Skripte, keine Client-Router-Magie.
  prefetch: false,
  devToolbar: { enabled: false },
  integrations: [
    sitemap({
      filter: (page) => !NOINDEX_PATHS.some((p) => page.endsWith(p)),
      changefreq: 'monthly',
    }),
  ],
});
