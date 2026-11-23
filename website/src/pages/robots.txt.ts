/**
 * robots.txt – wird beim Build mit der korrekten Sitemap-URL erzeugt.
 */
import type { APIRoute } from 'astro';
import { DEMO_MODE } from '../config/site';

export const GET: APIRoute = ({ site }) => {
  const sitemap = new URL('/sitemap-index.xml', site).href;
  const body = [
    'User-agent: *',
    ...(DEMO_MODE ? [] : ['Allow: /']),
    // Testversion: komplett sperren. Live: nur den Formular-Endpunkt.
    DEMO_MODE ? 'Disallow: /' : 'Disallow: /api/',
    '',
    `Sitemap: ${sitemap}`,
    '',
  ].join('\n');

  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
