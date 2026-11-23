/**
 * Läuft automatisch nach `astro build` (siehe package.json → "build").
 *
 * 1. Kopiert den PHP-Formular-Handler nach dist/api/ (inkl. PHPMailer-Dateien,
 *    ohne Entwicklungsabhängigkeiten).
 * 2. Kopiert die gemeinsame Formular-Definition nach dist/api/lib/.
 * 3. Erzeugt dist/.htaccess (Apache) mit HTTPS-Weiterleitung, Sicherheits-
 *    Headern, Caching und Kompression – Werte aus config/security-headers.json.
 * 4. Erzeugt deploy/nginx-security-headers.conf für nginx-Server.
 * 5. Prüft, dass kein Inline-Skript/-Style im Build steckt (sonst würde die
 *    strenge Content-Security-Policy die Seite beschädigen).
 */
import { cp, mkdir, readFile, readdir, writeFile, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');
const php = path.join(root, 'php');
const apiDir = path.join(dist, 'api');
const libDir = path.join(apiDir, 'lib');

const exists = (p) =>
  access(p).then(
    () => true,
    () => false,
  );

// 1. PHP-Handler ------------------------------------------------------------
const mailerSrc = path.join(php, 'vendor/phpmailer/phpmailer');
if (!(await exists(mailerSrc))) {
  console.error('\n✖ PHPMailer fehlt. Bitte zuerst ausführen:  composer install --working-dir=php\n');
  process.exit(1);
}

await mkdir(path.join(libDir, 'phpmailer'), { recursive: true });
await cp(path.join(php, 'public/kontakt.php'), path.join(apiDir, 'kontakt.php'));
await cp(path.join(php, 'bootstrap.php'), path.join(libDir, 'bootstrap.php'));
await cp(path.join(php, 'src'), path.join(libDir, 'src'), { recursive: true });
for (const file of ['PHPMailer.php', 'SMTP.php', 'Exception.php']) {
  await cp(path.join(mailerSrc, 'src', file), path.join(libDir, 'phpmailer', file));
}
await cp(path.join(mailerSrc, 'LICENSE'), path.join(libDir, 'phpmailer', 'LICENSE'));

// 2. Formular-Definition ----------------------------------------------------
await cp(path.join(root, 'src/config/contact-form.json'), path.join(libDir, 'form-config.json'));

// Bibliotheksordner vollständig sperren
await writeFile(path.join(libDir, '.htaccess'), '# Kein direkter Zugriff aus dem Internet\nRequire all denied\n');

// 3. .htaccess ----------------------------------------------------------------
const { headers } = JSON.parse(await readFile(path.join(root, 'config/security-headers.json'), 'utf8'));
const headerLines = Object.entries(headers)
  .map(([name, value]) => `  Header always set ${name} "${value.replaceAll('"', '\\"')}"`)
  .join('\n');

const htaccess = `# ============================================================================
# Apache-Konfiguration – AUTOMATISCH ERZEUGT durch scripts/postbuild.mjs
# Nicht hier bearbeiten: Änderungen in config/security-headers.json bzw. im
# Skript vornehmen und neu bauen.
# ============================================================================

Options -Indexes -MultiViews
DirectoryIndex index.html
AddDefaultCharset utf-8
ErrorDocument 404 /404.html

# --- MIME-Typen -------------------------------------------------------------
AddType font/woff2 .woff2
AddType image/avif .avif
AddType image/webp .webp
AddType application/manifest+json .webmanifest

<IfModule mod_rewrite.c>
  RewriteEngine On

  # HTTPS erzwingen (auch hinter Proxys/Load-Balancern des Hosters)
  RewriteCond %{HTTPS} !=on
  RewriteCond %{HTTP:X-Forwarded-Proto} !=https
  RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

  # Kanonische Domain erzwingen – nach Domain-Entscheidung EINE Variante aktivieren:
  # a) www → ohne www
  # RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]
  # RewriteRule ^ https://%1%{REQUEST_URI} [R=301,L]
  # b) ohne www → www
  # RewriteCond %{HTTP_HOST} !^www\\. [NC]
  # RewriteRule ^ https://www.%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

  # Versteckte Dateien (.git, .env …) sperren
  RewriteRule (^|/)\\. - [F,L]
</IfModule>

# --- Sensible Dateitypen sperren ------------------------------------------------
<FilesMatch "\\.(md|lock|log|ini|sh|sql|bak|old|orig|dist|example|phar|yml|yaml|env)$">
  Require all denied
</FilesMatch>
<FilesMatch "^(composer\\.(json|lock)|package(-lock)?\\.json|kontakt-config\\.php)$">
  Require all denied
</FilesMatch>

# --- Sicherheits-Header -------------------------------------------------------
<IfModule mod_headers.c>
${headerLines}
  Header always unset X-Powered-By
  Header unset X-Powered-By

  # Caching: HTML immer frisch prüfen, statische Dateien 1 Tag
  <FilesMatch "\\.html$">
    Header set Cache-Control "no-cache"
  </FilesMatch>
  <FilesMatch "\\.(png|jpe?g|webp|avif|svg|ico|webmanifest|xml|txt)$">
    Header set Cache-Control "public, max-age=86400"
  </FilesMatch>
</IfModule>

# --- Kompression ------------------------------------------------------------------
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml application/javascript text/javascript application/json application/xml image/svg+xml application/manifest+json
</IfModule>
`;
await writeFile(path.join(dist, '.htaccess'), htaccess);

// Dateien in /_astro/ tragen einen Inhalts-Hash im Namen → dürfen „ewig“ gecacht werden.
await writeFile(
  path.join(dist, '_astro', '.htaccess'),
  '<IfModule mod_headers.c>\n  Header set Cache-Control "public, max-age=31536000, immutable"\n</IfModule>\n',
);

// 4. nginx-Variante ---------------------------------------------------------------
await mkdir(path.join(root, 'deploy'), { recursive: true });
const nginx = `# AUTOMATISCH ERZEUGT durch scripts/postbuild.mjs – in den server{}-Block einbinden:
#   include /pfad/zu/nginx-security-headers.conf;
# Vollständiges Beispiel: deploy/nginx.conf.example
${Object.entries(headers)
  .map(([name, value]) => `add_header ${name} "${value}" always;`)
  .join('\n')}
`;
await writeFile(path.join(root, 'deploy/nginx-security-headers.conf'), nginx);

// 5. CSP-Selbstprüfung --------------------------------------------------------------
async function* htmlFiles(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(p);
    else if (entry.name.endsWith('.html')) yield p;
  }
}

const problems = [];
for await (const file of htmlFiles(dist)) {
  const html = await readFile(file, 'utf8');
  const rel = path.relative(dist, file);
  for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) {
    const attrs = m[1] ?? '';
    const body = (m[2] ?? '').trim();
    if (body && !/type="application\/ld\+json"/.test(attrs)) problems.push(`${rel}: Inline-<script>`);
  }
  if (/<style\b/.test(html)) problems.push(`${rel}: Inline-<style>`);
  if (/\sstyle="/.test(html)) problems.push(`${rel}: style-Attribut`);
  if (/\son[a-z]+="/.test(html)) problems.push(`${rel}: Inline-Eventhandler (on…=)`);
}

if (problems.length) {
  console.error('\n✖ Der Build enthält Inline-Code, den die Content-Security-Policy blockieren würde:');
  for (const p of problems) console.error('  - ' + p);
  process.exit(1);
}

console.log('✓ postbuild: PHP-Handler, .htaccess und nginx-Header erzeugt; keine CSP-Verstöße gefunden.');
