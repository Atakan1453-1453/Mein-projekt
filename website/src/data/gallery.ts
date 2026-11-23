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
 *  - `placeholder: true` entfernen, sobald ein echtes Foto eingesetzt ist.
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
  /** true = neutrales Platzhalterbild, vor dem Livegang ersetzen */
  placeholder?: boolean;
}

export const gallery: GalleryImage[] = [
  { src: aussenansicht, caption: 'Außenansicht', alt: 'Platzhalterbild: hier folgt ein Foto der Außenansicht', placeholder: true },
  { src: eingang, caption: 'Haupteingang', alt: 'Platzhalterbild: hier folgt ein Foto des Haupteingangs', placeholder: true },
  { src: ladenstrasse, caption: 'Ladenstraße', alt: 'Platzhalterbild: hier folgt ein Foto der Ladenstraße', placeholder: true },
  { src: schaufenster, caption: 'Schaufenster', alt: 'Platzhalterbild: hier folgt ein Foto eines Schaufensters', placeholder: true },
  { src: gastronomie, caption: 'Gastronomie', alt: 'Platzhalterbild: hier folgt ein Foto des Gastronomiebereichs', placeholder: true },
  { src: innenansicht, caption: 'Innenansicht', alt: 'Platzhalterbild: hier folgt eine Innenansicht', placeholder: true },
  { src: parkhaus, caption: 'Parkhaus', alt: 'Platzhalterbild: hier folgt ein Foto des Parkhauses', placeholder: true },
  { src: architektur, caption: 'Architekturdetail', alt: 'Platzhalterbild: hier folgt ein Architekturdetail', placeholder: true },
  { src: abend, caption: 'Abendstimmung', alt: 'Platzhalterbild: hier folgt eine Abendaufnahme', placeholder: true },
];
