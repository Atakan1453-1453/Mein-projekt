/**
 * Strukturierte Daten (schema.org, JSON-LD) für Suchmaschinen.
 * Es werden nur Felder ausgegeben, deren Werte bekannt sind – fehlende
 * Angaben (null) werden weggelassen statt erfunden.
 */
import { site, realOf } from '../config/site';

export function shoppingCenterJsonLd(siteUrl: URL | undefined): Record<string, unknown> {
  const base = siteUrl?.href ?? '/';
  const data: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'ShoppingCenter',
    '@id': `${base}#center`,
    name: `${site.name} ${site.city}`,
    description: site.description,
    url: base,
    image: new URL('/og-image.png', base).href,
    address: {
      '@type': 'PostalAddress',
      streetAddress: site.address.street,
      postalCode: site.address.postalCode,
      addressLocality: site.address.city,
      addressRegion: site.address.region,
      addressCountry: site.address.country,
    },
    openingHoursSpecification: site.openingHours.schema.map((spec) => ({
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: spec.days.map((d) => `https://schema.org/${d}`),
      opens: spec.opens,
      closes: spec.closes,
    })),
    amenityFeature: [
      { '@type': 'LocationFeatureSpecification', name: 'Parkhaus (über 400 Stellplätze, 24 h geöffnet)', value: true },
    ],
  };

  // Nur echte Angaben – fiktive Testwerte gehören nicht in die Suchmaschinen-Daten.
  const phone = realOf(site.contact.phone);
  const email = realOf(site.contact.email);
  if (phone) data['telephone'] = phone;
  if (email) data['email'] = email;

  return data;
}
