/**
 * Erzeugt einmalig statische Grafiken mit den Website-Schriften:
 *   - public/og-image.png          (Vorschaubild für Social Media, 1200×630)
 *   - public/apple-touch-icon.png  (180×180)
 *   - public/icon-192.png, icon-512.png (Web-App-Manifest)
 *   - public/favicon.ico           (32×32, PNG-in-ICO)
 *   - src/assets/gallery/platzhalter-*.jpg (neutrale Platzhalter für die Galerie)
 *
 * Aufruf:  npm run generate:assets
 * Benötigt: Playwright-Chromium (für Typografie) und sharp (Konvertierung).
 *
 * Die Galerie-Platzhalter sind bewusst als solche beschriftet. Sobald echte
 * Fotos vorliegen, werden sie NICHT mehr benötigt (siehe WARTUNG.md).
 */
import { chromium } from 'playwright';
import sharp from 'sharp';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const fontsDir = path.join(root, 'src/assets/fonts');
const publicDir = path.join(root, 'public');
const galleryDir = path.join(root, 'src/assets/gallery');

const fontCss = async () => {
  const f = (await readFile(path.join(fontsDir, 'fraunces-latin-wght-normal.woff2'))).toString('base64');
  const i = (await readFile(path.join(fontsDir, 'inter-latin-wght-normal.woff2'))).toString('base64');
  return `
    @font-face { font-family: 'Fraunces'; font-weight: 100 900; src: url(data:font/woff2;base64,${f}) format('woff2'); }
    @font-face { font-family: 'Inter'; font-weight: 100 900; src: url(data:font/woff2;base64,${i}) format('woff2'); }
    * { margin: 0; box-sizing: border-box; }
    body { font-family: Inter, sans-serif; -webkit-font-smoothing: antialiased; }
  `;
};

const crown = (stroke = '#d4b16a', fill = '#d4b16a') => `
  <path d="M11.5 27.5 10 16.5l5.3 4L20 12.5l4.7 8 5.3-4-1.5 11Z" fill="${fill}" stroke="${stroke}" stroke-width="1.6" stroke-linejoin="round"/>
  <path d="M11 31h18" stroke="${stroke}" stroke-width="1.6" stroke-linecap="round"/>`;

const arches = (w, h, opacity = 0.5) => {
  // Konzentrische Bögen als Hintergrundmotiv
  const cx = w * 0.78;
  const rings = [0.62, 0.5, 0.38, 0.26]
    .map((r, idx) => {
      const rr = h * r;
      return `<path d="M${cx - rr} ${h}V${h * 0.55}a${rr} ${rr} 0 0 1 ${rr * 2} 0V${h}" fill="none" stroke="#c49a48" stroke-width="2" opacity="${opacity - idx * 0.08}"/>`;
    })
    .join('');
  return rings;
};

async function render(page, html, width, height, out, { type = 'png', quality = 82 } = {}) {
  await page.setViewportSize({ width, height });
  await page.setContent(html, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const buf = await page.screenshot({ type: 'png' });
  const img = sharp(buf);
  if (type === 'jpg') await img.jpeg({ quality, mozjpeg: true }).toFile(out);
  else await img.png({ compressionLevel: 9, palette: false }).toFile(out);
  return buf;
}

const ogHtml = (css) => `<!doctype html><html><head><style>${css}
  body { width: 1200px; height: 630px; background: radial-gradient(80% 90% at 85% 10%, rgba(212,177,106,.22), transparent 60%), linear-gradient(160deg, #2c2456, #15112b); color: #fff; position: relative; overflow: hidden; }
  .wrap { position: absolute; left: 88px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; gap: 22px; width: 720px; }
  .eyebrow { font-size: 22px; letter-spacing: .22em; text-transform: uppercase; color: #e3c98f; font-weight: 650; display: flex; align-items: center; gap: 16px; }
  .eyebrow::before { content: ''; width: 48px; height: 2px; background: #d4b16a; }
  h1 { font-family: Fraunces, serif; font-weight: 520; font-size: 92px; line-height: 1; letter-spacing: -.02em; }
  p { font-size: 30px; color: #d9d4e8; }
  svg.bg { position: absolute; inset: 0; }
  svg.mark { width: 88px; height: 88px; }
</style></head><body>
  <svg class="bg" viewBox="0 0 1200 630" width="1200" height="630">${arches(1200, 630, 0.55)}</svg>
  <div class="wrap">
    <svg class="mark" viewBox="0 0 40 40"><path d="M6 38V18a14 14 0 0 1 28 0v20" fill="none" stroke="#c49a48" stroke-width="1.6"/>${crown()}</svg>
    <div class="eyebrow">Mettmann · Talstraße 10</div>
    <h1>Galerie Königshof</h1>
    <p>Shopping im Herzen der Stadt</p>
  </div>
</body></html>`;

const iconHtml = (css, size) => `<!doctype html><html><head><style>${css}
  body { width: ${size}px; height: ${size}px; background: linear-gradient(160deg, #2c2456, #15112b); display: grid; place-items: center; }
  svg { width: ${Math.round(size * 0.72)}px; height: ${Math.round(size * 0.72)}px; }
</style></head><body>
  <svg viewBox="0 0 40 40"><path d="M6 38V18a14 14 0 0 1 28 0v20" fill="none" stroke="#c49a48" stroke-width="1.8"/>${crown()}</svg>
</body></html>`;

const gallery = [
  { file: 'platzhalter-01-aussenansicht', label: 'Außenansicht' },
  { file: 'platzhalter-02-eingang', label: 'Haupteingang' },
  { file: 'platzhalter-03-ladenstrasse', label: 'Ladenstraße' },
  { file: 'platzhalter-04-schaufenster', label: 'Schaufenster' },
  { file: 'platzhalter-05-gastronomie', label: 'Gastronomie' },
  { file: 'platzhalter-06-innenansicht', label: 'Innenansicht' },
  { file: 'platzhalter-07-parkhaus', label: 'Parkhaus' },
  { file: 'platzhalter-08-architektur', label: 'Architekturdetail' },
  { file: 'platzhalter-09-abendstimmung', label: 'Abendstimmung' },
];

const galleryHtml = (css, label, n) => {
  const hue = [0, 18, -12, 8, -20, 14, -6, 22, -16][n % 9];
  return `<!doctype html><html><head><style>${css}
  body { width: 1600px; height: 1200px; position: relative; overflow: hidden; color: #f5f2fb;
    background: radial-gradient(70% 70% at 50% 18%, rgba(212,177,106,.28), transparent 62%), linear-gradient(170deg, hsl(${252 + hue} 40% 30%), #15112b); }
  svg { position: absolute; inset: 0; }
  .label { position: absolute; left: 0; right: 0; bottom: 120px; text-align: center; display: grid; gap: 18px; }
  .tag { justify-self: center; font-size: 26px; letter-spacing: .24em; text-transform: uppercase; color: #e3c98f; font-weight: 650; border: 2px dashed #d4b16a; padding: 10px 22px; border-radius: 10px; }
  h2 { font-family: Fraunces, serif; font-weight: 500; font-size: 96px; letter-spacing: -.01em; }
  p { font-size: 30px; color: #cfc9e4; }
</style></head><body>
  <svg viewBox="0 0 1600 1200" width="1600" height="1200">
    <path d="M300 1200V560a500 500 0 0 1 1000 0v640" fill="none" stroke="#c49a48" stroke-width="3" opacity=".55"/>
    <path d="M380 1200V575a420 420 0 0 1 840 0v625" fill="none" stroke="#c49a48" stroke-width="2" opacity=".35"/>
    <g transform="translate(728 250) scale(3.6)" opacity=".9">${crown()}</g>
  </svg>
  <div class="label">
    <span class="tag">Platzhalter · Foto folgt</span>
    <h2>${label}</h2>
    <p>Galerie Königshof Mettmann</p>
  </div>
</body></html>`;
};

/** Baut eine .ico-Datei, die ein PNG enthält (von allen Browsern unterstützt). */
function pngToIco(png, size) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2); // Typ: Icon
  header.writeUInt16LE(1, 4); // Anzahl Bilder
  const entry = Buffer.alloc(16);
  entry.writeUInt8(size >= 256 ? 0 : size, 0);
  entry.writeUInt8(size >= 256 ? 0 : size, 1);
  entry.writeUInt8(0, 2);
  entry.writeUInt8(0, 3);
  entry.writeUInt16LE(1, 4);
  entry.writeUInt16LE(32, 6);
  entry.writeUInt32LE(png.length, 8);
  entry.writeUInt32LE(6 + 16, 12);
  return Buffer.concat([header, entry, png]);
}

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });
const css = await fontCss();

await mkdir(publicDir, { recursive: true });
await mkdir(galleryDir, { recursive: true });

await render(page, ogHtml(css), 1200, 630, path.join(publicDir, 'og-image.png'));
await render(page, iconHtml(css, 180), 180, 180, path.join(publicDir, 'apple-touch-icon.png'));
await render(page, iconHtml(css, 192), 192, 192, path.join(publicDir, 'icon-192.png'));
await render(page, iconHtml(css, 512), 512, 512, path.join(publicDir, 'icon-512.png'));
const favPng = await render(page, iconHtml(css, 32), 32, 32, path.join(root, '.tmp-favicon.png'));
await writeFile(path.join(publicDir, 'favicon.ico'), pngToIco(await sharp(favPng).png().toBuffer(), 32));

for (const [n, item] of gallery.entries()) {
  await render(page, galleryHtml(css, item.label, n), 1600, 1200, path.join(galleryDir, `${item.file}.jpg`), {
    type: 'jpg',
  });
}

await browser.close();
const { rm } = await import('node:fs/promises');
await rm(path.join(root, '.tmp-favicon.png'), { force: true });
console.log('Grafiken erzeugt.');
