# Sprecherspur Verdun 1916

* Stimme: ElevenLabs v4 „Alistair“ über Higgsfield (`config/voice.txt`), 73 Absätze = 73 Dateien `P01.mp3 … P73.mp3`
  (Original-Downloads; Job-IDs in `../voice_jobs.json`, Datei-URLs in `urls.txt`).
* Bearbeitung für den Schnitt (`P??.wav`, nicht im Repo, wird per Skript erzeugt): Stille am Anfang/Ende entfernt,
  Pausen > 0,5 s auf 0,42 s gekürzt, Tempo +6 % (ffmpeg atempo 1.06, Tonhöhe bleibt).
* Kontrolle 5.11.2026: alle Absätze per Spracherkennung (faster-whisper „small“) abgehört → vollständig,
  keine Aussetzer. Ortsnamen werden wie gewünscht gesprochen (z. B. „Wer-döng“, „Pe-täng“, „Woa Sa-kreh“,
  „Courage ! On les aura !“). Keine Neuaufnahme nötig.

## Shorts-Hooks (ElevenLabs v4, Alistair)

| Datei | Job | Text (TTS-Schreibweise) |
|---|---|---|
| S1.mp3 | 48eca43e-1efe-46dc-a6a4-2d0d66cf9a31 | Das größte Fort von Wer-döng. Erobert, ohne dass ein einziger Schuss fällt. Fünfundzwanzigster Februar neunzehnhundertsechzehn. |
| S2.mp3 | de62df31-d86e-4d36-a6e6-f4ae2ca758f7 | Eine einzige Landstraße hat Frankreich gerettet. Wer-döng, Februar neunzehnhundertsechzehn. General Pe-täng soll die Stadt halten. |
| S3.mp3 | 8906b356-3819-4ecf-acf2-483db6035e45 | Zehn Monate Hölle. Rund dreihunderttausend Tote. Und am Ende fast kein Meter gewonnen. |
| SO.mp3 | bcf07ee8-1aca-4161-99eb-900f4343615c | Die ganze Geschichte der Schlacht um Wer-döng siehst du auf War A Zett. |

Aufbereitung: `python3 shorts.py prep` (Stille kürzen, atempo 1.06 → S*.wav, nicht im Repo).
