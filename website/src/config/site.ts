/**
 * ZENTRALE FIRMEN- UND INHALTSDATEN
 * ==================================
 * Hier stehen alle Fakten, die auf der Website erscheinen. Wer Texte oder
 * Angaben ändern möchte, muss in der Regel nur diese Datei anpassen.
 *
 * Regel für den Livegang: KEINE Angaben erfinden. Unbekannte Werte stehen auf
 * `null` (→ sichtbarer Platzhalter) oder – in der Testversion – auf einem
 * fiktiven `demo('…')`-Wert. `npm run check:launch` schlägt fehl, solange
 * Platzhalter ODER fiktive Werte vorhanden sind.
 *
 * Quellen der bereits eingetragenen Fakten (Recherche Oktober 2026, siehe
 * README.md im Hauptverzeichnis): Center-Website galeriekoenigshof.de,
 * Stadt Mettmann, ILG Gruppe, Radio Neandertal, Schaufenster Mettmann,
 * Gleeds, Phoenix Development.
 * → Vor dem Livegang ALLE Angaben vom Center-Management bestätigen lassen.
 */

/**
 * TESTVERSION
 * -----------
 * `DEMO_MODE = true` kennzeichnet diesen Stand als Testversion mit FIKTIVEN
 * Beispielangaben (Mustermann, Musterstadt, example.com …). Dann gilt:
 *  - Hinweisbalken „Testversion“ auf jeder Seite,
 *  - alle Seiten auf noindex, robots.txt sperrt Suchmaschinen,
 *  - `npm run check:launch` schlägt fehl.
 * Für den Livegang: alle `demo(…)`-Werte durch echte Angaben ersetzen und
 * DEMO_MODE auf false setzen.
 */
export const DEMO_MODE = true;

/** Fiktiver Beispielwert – erscheint normal, wird aber als „Demo“ markiert. */
export type DemoValue = { readonly demo: string };
export const demo = (value: string): DemoValue => ({ demo: value });

/** Ein Wert, der noch vom Center-Management geliefert werden muss (null = Platzhalter). */
export type Pending = string | DemoValue | null;

/** Text eines Wertes – egal ob echt oder fiktiv. */
export const textOf = (value: Pending): string | null => (value === null ? null : typeof value === 'string' ? value : value.demo);
/** Nur echte (nicht fiktive) Werte, z. B. für strukturierte Daten. */
export const realOf = (value: Pending): string | null => (typeof value === 'string' ? value : null);

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

  /** Kontaktdaten des Center-Managements – FIKTIV (Testversion). */
  contact: {
    // Nicht vergebbare Nummer (Teilnehmernummern beginnen in DE nie mit 0)
    phone: demo('+49 2104 0000000') as Pending,
    // example.com ist für Beispiele reserviert (RFC 2606) – kommt nirgends an
    email: demo('center@example.com') as Pending,
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
    /** Parkgebühren – FIKTIV (Testversion). */
    fees: demo('erste 30 Minuten frei, danach 1,00 € je angefangene Stunde, Tageshöchstsatz 8,00 €') as Pending,
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
   * IMPRESSUM-ANGABEN (§ 5 DDG) – müssen für den Livegang vom Betreiber kommen.
   * Aktuell: FIKTIVE Musterdaten (Testversion).
   */
  operator: {
    legalName: demo('Muster Center-Management GmbH') as Pending, // vollständiger Name inkl. Rechtsform
    street: demo('Musterstraße 1') as Pending,
    postalCode: demo('12345') as Pending,
    city: demo('Musterstadt') as Pending,
    representatives: demo('Max Mustermann (Geschäftsführer)') as Pending, // vertretungsberechtigte Person(en)
    phone: demo('+49 2104 0000000') as Pending,
    email: demo('impressum@example.com') as Pending,
    registerCourt: demo('Amtsgericht Musterstadt') as Pending,
    registerNumber: demo('HRB 00000') as Pending,
    vatId: demo('DE000000000') as Pending, // USt-IdNr. nach § 27a UStG, falls vorhanden
    /** Verantwortlich für redaktionelle Inhalte (§ 18 Abs. 2 MStV). */
    editorialResponsible: demo('Erika Mustermann, Musterstraße 1, 12345 Musterstadt') as Pending,
  },

  /** Angaben für die Datenschutzerklärung – aktuell FIKTIV (Testversion). */
  privacy: {
    hostingProvider: demo('Muster-Hosting GmbH, Beispielweg 2, 12345 Musterstadt') as Pending, // Webhoster
    mailProvider: demo('Muster-Mail GmbH, Beispielweg 3, 12345 Musterstadt') as Pending, // E-Mail-Anbieter
    dataProtectionOfficer: demo('Datenschutzbeauftragte: Erika Musterfrau, datenschutz@example.com') as Pending,
    logRetentionDays: demo('7') as Pending, // Speicherdauer Server-Logfiles laut Hoster
    /** Stand der Datenschutzerklärung – bei jeder Änderung aktualisieren. */
    lastUpdated: 'November 2026',
  },

  /**
   * Fiktive Beispiel-Inhalte für Blöcke, zu denen noch Angaben fehlen
   * (Testversion). Für den Livegang durch echte Inhalte ersetzen.
   */
  demoContent: {
    management: [
      { name: 'Erika Mustermann', role: 'Center-Managerin', text: 'Ansprechpartnerin für Mieter, Kooperationen und alle Fragen rund um das Center.' },
      { name: 'Max Mustermann', role: 'Vermietung & Marketing', text: 'Ansprechpartner für Mietflächen, Werbung und Aktionen im Center.' },
    ],
    services: [
      { title: 'Barrierefreier Zugang', text: 'Stufenlose Eingänge und Aufzüge zwischen Parkhaus und Ladenstraße.' },
      { title: 'Kundentoiletten & Wickelraum', text: 'Im Erdgeschoss, gut ausgeschildert.' },
      { title: 'Fundsachen', text: 'Verloren oder gefunden? Wenden Sie sich an das Center-Management.' },
      { title: 'Kostenloses WLAN', text: 'Gast-WLAN in der gesamten Ladenstraße.' },
    ],
    consumerDisputes:
      'Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.',
    imageCredits: 'Symbolgrafiken: eigene Gestaltung (Testversion, keine Fotos des Centers).',
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
