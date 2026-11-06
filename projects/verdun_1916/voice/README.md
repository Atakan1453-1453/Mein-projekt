# Sprecherspur Verdun 1916

* Stimme: ElevenLabs v4 „Alistair“ über Higgsfield (`config/voice.txt`), 73 Absätze = 73 Dateien `P01.mp3 … P73.mp3`
  (Original-Downloads; Job-IDs in `../voice_jobs.json`, Datei-URLs in `urls.txt`).
* Bearbeitung für den Schnitt (`P??.wav`, nicht im Repo, wird per Skript erzeugt): Stille am Anfang/Ende entfernt,
  Pausen > 0,5 s auf 0,42 s gekürzt, Tempo +6 % (ffmpeg atempo 1.06, Tonhöhe bleibt).
* Kontrolle 5.11.2026: alle Absätze per Spracherkennung (faster-whisper „small“) abgehört → vollständig,
  keine Aussetzer. Ortsnamen werden wie gewünscht gesprochen (z. B. „Wer-döng“, „Pe-täng“, „Woa Sa-kreh“,
  „Courage ! On les aura !“). Keine Neuaufnahme nötig.
