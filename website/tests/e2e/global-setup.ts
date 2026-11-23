import { rm, access } from 'node:fs/promises';

/** Vor jedem Testlauf: Test-Speicher (Rate-Limit, Test-Mails) leeren, Build prüfen. */
export default async function globalSetup(): Promise<void> {
  try {
    await access('dist/index.html');
    await access('dist/api/kontakt.php');
  } catch {
    throw new Error('Kein Build gefunden. Bitte zuerst „npm run build“ ausführen.');
  }
  await rm('.tmp/test-storage', { recursive: true, force: true });
}
