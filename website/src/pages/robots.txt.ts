/**
 * robots.txt – wird beim Build mit der korrekten Sitemap-URL erzeugt.
 */
import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ site }) => {
  const sitemap = new URL('/sitemap-index.xml', site).href;
  const body = [
    'User-agent: *',
    'Allow: /',
    // Formular-Endpunkt und Statusseiten haben in Suchmaschinen nichts verloren.
    'Disallow: /api/',
    '',
    `Sitemap: ${sitemap}`,
    '',
  ].join('\n');

  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
