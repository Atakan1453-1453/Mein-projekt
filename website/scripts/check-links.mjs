/**
 * Linkprüfung für den fertigen Build (dist/):
 *  - Jeder interne Link (href, src, srcset, Canonical/OG-Bild) muss auf eine
 *    vorhandene Datei bzw. Seite zeigen.
 *  - Sprungmarken (#anker) müssen auf der Zielseite existieren.
 *  - Externe Links werden aufgelistet und – wenn das Netzwerk es erlaubt –
 *    per HEAD/GET geprüft (mit --external).
 *
 *   npm run check:links             # nur intern (schnell, offline)
 *   npm run check:links -- --external
 */
import { readdir, readFile, stat } from 'node:fs/promises';
import { parse } from 'node-html-parser';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');
const checkExternal = process.argv.includes('--external');

const SITE_URL = (process.env.SITE_URL ?? 'https://galeriekoenigshof.de').replace(/\/$/, '');

async function* walk(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else if (e.name.endsWith('.html')) yield p;
  }
}

const isFile = (p) => stat(p).then((s) => s.isFile(), () => false);

/** URL-Pfad → Datei in dist (wie der Webserver es auflösen würde) */
async function resolveTarget(urlPath) {
  const clean = decodeURIComponent(urlPath.split('?')[0]);
  if (clean.endsWith('/')) return (await isFile(path.join(dist, clean, 'index.html'))) ? path.join(dist, clean, 'index.html') : null;
  if (await isFile(path.join(dist, clean))) return path.join(dist, clean);
  return null;
}

const pages = new Map(); // Datei → geparstes Dokument
for await (const file of walk(dist)) pages.set(file, parse(await readFile(file, 'utf8')));

const errors = [];
const external = new Map(); // URL → Fundstellen

for (const [file, doc] of pages) {
  const from = '/' + path.relative(dist, file).replace(/index\.html$/, '');
  const refs = [];
  for (const el of doc.querySelectorAll('[href]')) refs.push(el.getAttribute('href'));
  for (const el of doc.querySelectorAll('[src]')) refs.push(el.getAttribute('src'));
  for (const el of doc.querySelectorAll('[srcset]')) {
    for (const part of el.getAttribute('srcset').split(',')) refs.push(part.trim().split(/\s+/)[0]);
  }
  for (const el of doc.querySelectorAll('meta[property="og:image"], meta[property="og:url"]')) refs.push(el.getAttribute('content'));
  for (const el of doc.querySelectorAll('form[action]')) refs.push(el.getAttribute('action'));

  for (let ref of refs) {
    if (!ref || ref.startsWith('mailto:') || ref.startsWith('tel:') || ref.startsWith('data:')) continue;
    if (ref.startsWith(SITE_URL)) ref = ref.slice(SITE_URL.length) || '/';
    if (/^https?:\/\//.test(ref)) {
      external.set(ref, [...(external.get(ref) ?? []), from]);
      continue;
    }
    if (ref.startsWith('#')) {
      const id = ref.slice(1);
      if (id && !doc.getElementById(id)) errors.push(`${from}: Sprungmarke ${ref} existiert nicht`);
      continue;
    }
    const absolute = new URL(ref, 'http://x' + from);
    if (absolute.pathname === '/api/kontakt.php') {
      if (!(await isFile(path.join(dist, 'api/kontakt.php')))) errors.push(`${from}: Formular-Endpunkt fehlt`);
      continue;
    }
    const target = await resolveTarget(absolute.pathname);
    if (!target) {
      errors.push(`${from}: Link-Ziel nicht gefunden → ${ref}`);
      continue;
    }
    if (absolute.hash && target.endsWith('.html')) {
      const targetDoc = pages.get(target);
      const id = decodeURIComponent(absolute.hash.slice(1));
      if (targetDoc && !targetDoc.getElementById(id)) errors.push(`${from}: Sprungmarke ${ref} existiert auf der Zielseite nicht`);
    }
  }
}

console.log(`Geprüft: ${pages.size} Seiten.`);
console.log(`Externe Links (${external.size}):`);
for (const [url, where] of external) console.log(`  ${url}  ← ${[...new Set(where)].join(', ')}`);

if (checkExternal) {
  for (const url of external.keys()) {
    try {
      let res = await fetch(url, { method: 'HEAD', redirect: 'follow', signal: AbortSignal.timeout(10000) });
      if (res.status === 405 || res.status === 403) res = await fetch(url, { redirect: 'follow', signal: AbortSignal.timeout(10000) });
      if (res.status >= 400) errors.push(`Externer Link liefert HTTP ${res.status}: ${url}`);
      else console.log(`  ✓ ${res.status} ${url}`);
    } catch (e) {
      errors.push(`Externer Link nicht erreichbar: ${url} (${e.message})`);
    }
  }
}

if (errors.length) {
  console.error(`\n✖ ${errors.length} Problem(e):`);
  for (const e of errors) console.error('  - ' + e);
  process.exit(1);
}
console.log('\n✓ Alle internen Links und Sprungmarken sind gültig.');
