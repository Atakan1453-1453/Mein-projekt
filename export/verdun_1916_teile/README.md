# Verdun 1916 – Hauptvideo (Master in Teilen)

GitHub erlaubt höchstens 100 MB pro Datei. Darum liegt das Master-Video (866 MB, 1920×1080, 30 fps, H.264 crf 17, AAC 320k, −14 LUFS)
hier in 95-MB-Teilen.

Zusammensetzen:

- **macOS / Linux:** `cat verdun_1916.mp4.part* > verdun_1916.mp4`
- **Windows (Eingabeaufforderung):** `copy /b verdun_1916.mp4.part00+verdun_1916.mp4.part01+verdun_1916.mp4.part02+verdun_1916.mp4.part03+verdun_1916.mp4.part04+verdun_1916.mp4.part05+verdun_1916.mp4.part06+verdun_1916.mp4.part07+verdun_1916.mp4.part08+verdun_1916.mp4.part09 verdun_1916.mp4`

Prüfen (optional): `sha256sum -c verdun_1916.mp4.sha256` (macOS: `shasum -a 256 -c verdun_1916.mp4.sha256`)
