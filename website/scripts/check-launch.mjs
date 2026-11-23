/**
 * GO-LIVE-PRÜFUNG – vor jeder Veröffentlichung ausführen:
 *
 *   SITE_URL=https://www.ihre-domain.de npm run build && npm run check:launch
 *
 * Schlägt fehl, solange
 *  - noch Platzhalter ([data-placeholder]) im Build stehen,
 *  - Galeriebilder als Platzhalter markiert sind,
 *  - wichtige Dateien fehlen (.htaccess, robots.txt, Sitemap, PHP-Handler).
 * Gibt außerdem Hinweise auf manuell zu prüfende Punkte aus.
 */
import { readdir, readFile, access } from 'node:fs/promises';
import { parse } from 'node-html-parser';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');

async function* walk(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else if (e.name.endsWith('.html')) yield p;
  }
}

const blockers = [];
const placeholders = new Map(); // Platzhalter → Seiten

for await (const file of walk(dist)) {
  const page = '/' + path.relative(dist, file).replace(/index\.html$/, '');
  const doc = parse(await readFile(file, 'utf8'));
  for (const el of doc.querySelectorAll('[data-placeholder]')) {
    const label = el.getAttribute('data-placeholder');
    placeholders.set(label, new Set([...(placeholders.get(label) ?? []), page]));
  }
}

for (const [label, where] of placeholders) blockers.push(`Platzhalter „${label}“ auf: ${[...where].join(', ')}`);

for (const required of ['.htaccess', 'robots.txt', 'sitemap-index.xml', 'api/kontakt.php', 'api/lib/.htaccess', 'og-image.png']) {
  try {
    await access(path.join(dist, required));
  } catch {
    blockers.push(`Datei fehlt im Build: ${required}`);
  }
}

const robots = await readFile(path.join(dist, 'robots.txt'), 'utf8').catch(() => '');
const sitemapUrl = robots.match(/Sitemap: (\S+)/)?.[1] ?? '';
console.log(`Kanonische Domain laut Build: ${new URL(sitemapUrl || 'https://unbekannt').origin}`);
console.log('  → Stimmt das mit der echten Domain überein? Sonst mit SITE_URL=… neu bauen.\n');

if (blockers.length) {
  console.error(`✖ ${blockers.length} offene Punkt(e) – die Website ist noch NICHT bereit für den Livegang:\n`);
  for (const b of blockers) console.error('  - ' + b);
  console.error('\nAlle Angaben stehen in src/config/site.ts bzw. src/data/gallery.ts. Siehe GO-LIVE-CHECKLISTE.md.');
  process.exit(1);
}

console.log('✓ Keine Platzhalter mehr im Build.');
console.log('Bitte zusätzlich die manuellen Punkte in GO-LIVE-CHECKLISTE.md abarbeiten.');
