/**
 * GALERIE-BILDER
 * ==============
 * Neue Fotos: Datei nach src/assets/gallery/ legen, hier importieren und
 * einen Eintrag ergänzen. Astro erzeugt beim Build automatisch optimierte
 * AVIF/WebP-Varianten in mehreren Größen.
 *
 * Wichtig:
 *  - Nur Fotos verwenden, für die Nutzungsrechte vorliegen.
 *  - Erkennbare Personen nur mit deren Einwilligung (DSGVO / KUG).
 *  - `alt` beschreibt, was auf dem Bild zu sehen ist (für Screenreader).
 *  - `demo: true` entfernen, sobald ein echtes Foto eingesetzt ist.
 */
import type { ImageMetadata } from 'astro';
import aussenansicht from '../assets/gallery/platzhalter-01-aussenansicht.jpg';
import eingang from '../assets/gallery/platzhalter-02-eingang.jpg';
import ladenstrasse from '../assets/gallery/platzhalter-03-ladenstrasse.jpg';
import schaufenster from '../assets/gallery/platzhalter-04-schaufenster.jpg';
import gastronomie from '../assets/gallery/platzhalter-05-gastronomie.jpg';
import innenansicht from '../assets/gallery/platzhalter-06-innenansicht.jpg';
import parkhaus from '../assets/gallery/platzhalter-07-parkhaus.jpg';
import architektur from '../assets/gallery/platzhalter-08-architektur.jpg';
import abend from '../assets/gallery/platzhalter-09-abendstimmung.jpg';

export interface GalleryImage {
  src: ImageMetadata;
  alt: string;
  caption: string;
  /** true = Symbolgrafik der Testversion (kein echtes Foto), vor dem Livegang ersetzen */
  demo?: boolean;
}

export const gallery: GalleryImage[] = [
  { src: aussenansicht, caption: 'Außenansicht', alt: 'Symbolgrafik zum Thema Außenansicht (Testversion, kein Foto)', demo: true },
  { src: eingang, caption: 'Haupteingang', alt: 'Symbolgrafik zum Thema Haupteingang (Testversion, kein Foto)', demo: true },
  { src: ladenstrasse, caption: 'Ladenstraße', alt: 'Symbolgrafik zum Thema Ladenstraße (Testversion, kein Foto)', demo: true },
  { src: schaufenster, caption: 'Schaufenster', alt: 'Symbolgrafik zum Thema Schaufenster (Testversion, kein Foto)', demo: true },
  { src: gastronomie, caption: 'Gastronomie', alt: 'Symbolgrafik zum Thema Gastronomie (Testversion, kein Foto)', demo: true },
  { src: innenansicht, caption: 'Innenansicht', alt: 'Symbolgrafik zum Thema Innenansicht (Testversion, kein Foto)', demo: true },
  { src: parkhaus, caption: 'Parkhaus', alt: 'Symbolgrafik zum Thema Parkhaus (Testversion, kein Foto)', demo: true },
  { src: architektur, caption: 'Architekturdetail', alt: 'Symbolgrafik zum Thema Architekturdetail (Testversion, kein Foto)', demo: true },
  { src: abend, caption: 'Abendstimmung', alt: 'Symbolgrafik zum Thema Abendstimmung (Testversion, kein Foto)', demo: true },
];
