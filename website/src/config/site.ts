/**
 * ZENTRALE FIRMEN- UND INHALTSDATEN
 * ==================================
 * Hier stehen alle Fakten, die auf der Website erscheinen. Wer Texte oder
 * Angaben ändern möchte, muss in der Regel nur diese Datei anpassen.
 *
 * Regel: Es werden KEINE Angaben erfunden. Unbekannte Werte stehen auf `null`
 * und erscheinen auf der Website als deutlich markierter Platzhalter.
 * `npm run check:launch` listet alle offenen Platzhalter auf und schlägt fehl,
 * solange noch welche vorhanden sind.
 *
 * Quellen der bereits eingetragenen Fakten (Recherche Oktober 2026, siehe
 * README.md im Hauptverzeichnis): Center-Website galeriekoenigshof.de,
 * Stadt Mettmann, ILG Gruppe, Radio Neandertal, Schaufenster Mettmann,
 * Gleeds, Phoenix Development.
 * → Vor dem Livegang ALLE Angaben vom Center-Management bestätigen lassen.
 */

/** Ein Wert, der noch vom Center-Management geliefert werden muss. */
export type Pending<T = string> = T | null;

export const site = {
  name: 'Galerie Königshof',
  city: 'Mettmann',
  /** Wird in Seitentiteln verwendet: „Seite | Galerie Königshof Mettmann“. */
  titleSuffix: 'Galerie Königshof Mettmann',
  tagline: 'Shopping im Herzen der Stadt',
  description:
    'Die Galerie Königshof in Mettmann: über 20 Shops, Gastronomie und Services an der Talstraße – mit eigenem Parkhaus und über 400 Stellplätzen.',
  locale: 'de_DE',
  lang: 'de',

  address: {
    street: 'Talstraße 10',
    postalCode: '40822',
    city: 'Mettmann',
    region: 'Nordrhein-Westfalen',
    country: 'DE',
  },

  /** Kontaktdaten des Center-Managements – noch nicht bekannt. */
  contact: {
    phone: null as Pending, // z. B. '+49 2104 000000' (Anzeige) – bitte liefern
    email: null as Pending, // öffentliche Kontaktadresse – bitte liefern
  },

  /** Kernöffnungszeiten laut Center-Website. */
  openingHours: {
    days: 'Montag – Samstag',
    time: '10:00 – 19:00 Uhr',
    note: 'Kernöffnungszeiten. Einzelne Shops können abweichende Öffnungszeiten haben.',
    /** Maschinenlesbar für strukturierte Daten (schema.org). */
    schema: [{ days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], opens: '10:00', closes: '19:00' }],
  },

  /** Kennzahlen (Center-Website bzw. Projektangaben). */
  stats: [
    { value: '20+', label: 'Shops', detail: 'plus Gastronomie und Services' },
    { value: '400+', label: 'Parkplätze', detail: 'im eigenen Parkhaus' },
    { value: '15.000', label: 'm² Mietfläche', detail: 'circa, Gesamtfläche des Centers' },
  ],

  parking: {
    summary: 'Über 400 Stellplätze direkt am Center',
    facts: [
      { title: 'Über 400 Parkplätze', text: 'im Parkhaus der Galerie Königshof' },
      { title: 'Schrankenlos', text: 'Ein- und Ausfahrt ohne Schranke' },
      { title: 'Bezahlen am Automaten oder per App', text: 'Parkgebühr wahlweise am Automaten oder digital bezahlen' },
      { title: '24 Stunden geöffnet', text: 'das Parkhaus ist rund um die Uhr zugänglich' },
    ],
    /** Parkgebühren sind nicht bekannt → Platzhalter. */
    fees: null as Pending,
  },

  history: [
    { year: '1972', title: 'Kaufhaus an der Talstraße', text: 'Das Gebäude entsteht als Kaufhaus – später ist hier Hertie ansässig, bis 2009.' },
    { year: 'nach 2009', title: 'Umbau zur Königshof-Galerie', text: 'Das frühere Hertie-Areal wird zur Königshof-Galerie umgebaut.' },
    { year: '2019', title: 'Neustart als Galerie Königshof', text: 'Wiedereröffnung am 7. November 2019 nach 14 Monaten Umbau im laufenden Betrieb und einer Investition von über 10 Millionen Euro.' },
  ],

  /**
   * Shop-Auswahl laut Shop-Verzeichnis der Center-Website (Stand der Recherche).
   * Das Mieterangebot ändert sich – Liste vor dem Livegang abgleichen.
   */
  shopsAsOf: 'Oktober 2026',
  shops: [
    { name: 'H&M', category: 'Mode' },
    { name: 'Takko Fashion', category: 'Mode' },
    { name: "Ernsting's family", category: 'Mode' },
    { name: 'Deichmann', category: 'Schuhe' },
    { name: 'dm', category: 'Drogerie' },
    { name: 'easyApotheke', category: 'Gesundheit' },
    { name: 'Thalia', category: 'Bücher' },
    { name: 'Ambiente Blumen & mehr', category: 'Blumen' },
    { name: 'kkiosk', category: 'Presse & Tabak' },
    { name: 'Asia Friends', category: 'Gastronomie' },
  ],

  /**
   * IMPRESSUM-ANGABEN (§ 5 DDG) – müssen vom Betreiber kommen.
   * Nichts davon darf geschätzt werden.
   */
  operator: {
    legalName: null as Pending, // vollständiger Name inkl. Rechtsform, z. B. „Muster Center GmbH“
    street: null as Pending,
    postalCode: null as Pending,
    city: null as Pending,
    representatives: null as Pending, // vertretungsberechtigte Person(en), z. B. Geschäftsführung
    phone: null as Pending,
    email: null as Pending,
    registerCourt: null as Pending, // z. B. „Amtsgericht Düsseldorf“
    registerNumber: null as Pending, // z. B. „HRB 12345“
    vatId: null as Pending, // USt-IdNr. nach § 27a UStG, falls vorhanden
    /** Verantwortlich für redaktionelle Inhalte (§ 18 Abs. 2 MStV). */
    editorialResponsible: null as Pending,
  },

  /** Angaben für die Datenschutzerklärung. */
  privacy: {
    hostingProvider: null as Pending, // Name + Anschrift des Webhosters
    mailProvider: null as Pending, // Anbieter des E-Mail-Postfachs, an das Anfragen gehen
    dataProtectionOfficer: null as Pending, // Kontakt Datenschutzbeauftragte/r ODER „nicht benannt“
    logRetentionDays: null as Pending, // Speicherdauer Server-Logfiles laut Hoster, z. B. „7“
    /** Stand der Datenschutzerklärung – bei jeder Änderung aktualisieren. */
    lastUpdated: 'November 2026',
  },

  /** Externe Links (werden nur als normale Links eingebunden, ohne Einbettung). */
  links: {
    map: 'https://www.openstreetmap.org/search?query=Talstra%C3%9Fe%2010%2C%2040822%20Mettmann',
  },
} as const;

/** Hauptnavigation – Reihenfolge = Reihenfolge im Menü. */
export const navigation = [
  { href: '/', label: 'Start' },
  { href: '/ueber-uns/', label: 'Über uns' },
  { href: '/shops/', label: 'Shops & Services' },
  { href: '/galerie/', label: 'Galerie' },
  { href: '/kontakt/', label: 'Kontakt' },
] as const;

export const legalNavigation = [
  { href: '/impressum/', label: 'Impressum' },
  { href: '/datenschutz/', label: 'Datenschutz' },
] as const;

export const fullAddress = `${site.address.street}, ${site.address.postalCode} ${site.address.city}`;
