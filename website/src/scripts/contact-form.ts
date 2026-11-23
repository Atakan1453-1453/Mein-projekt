/**
 * Progressive Verbesserung des Kontaktformulars.
 *
 * Ohne dieses Skript funktioniert das Formular trotzdem (Browser-Validierung
 * + klassischer POST). Mit Skript:
 *  1. holt es ein signiertes Zeit-Token vom Server (Spam-Schutz: zu schnelles
 *     Absenden = Bot),
 *  2. zeigt Fehlermeldungen verständlich direkt am Feld + Fehlerübersicht,
 *  3. sendet per fetch und leitet bei Erfolg auf die Danke-Seite weiter,
 *  4. blendet die Zusatzfelder für Mietanfragen nur bei Bedarf ein,
 *  5. übernimmt eine Vorauswahl des Anliegens aus der URL (?anliegen=…).
 *
 * Die eigentliche, verbindliche Prüfung erfolgt IMMER auf dem Server.
 */
import formConfig from '../config/contact-form.json';

type FieldName = keyof typeof formConfig.fields;
type ServerResponse = { ok: boolean; errors?: Partial<Record<FieldName | 'form', string>>; redirect?: string };

const LABELS: Record<string, string> = {
  anliegen: 'Ihr Anliegen',
  name: 'Name',
  email: 'E-Mail-Adresse',
  telefon: 'Telefon',
  nachricht: 'Ihre Nachricht',
};

function messageFor(el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement): string {
  const v = el.validity;
  const label = LABELS[el.name] ?? 'Dieses Feld';
  if (v.valueMissing) {
    return el.tagName === 'SELECT' ? 'Bitte wählen Sie Ihr Anliegen aus.' : `Bitte geben Sie ${articleFor(el.name)} ein.`;
  }
  if (v.typeMismatch && el.type === 'email') return 'Bitte geben Sie eine gültige E-Mail-Adresse ein, z. B. name@beispiel.de.';
  if (v.tooShort && 'minLength' in el) return `${label}: bitte mindestens ${el.minLength} Zeichen eingeben (aktuell ${el.value.length}).`;
  if (v.tooLong && 'maxLength' in el) return `${label}: bitte höchstens ${el.maxLength} Zeichen eingeben.`;
  if (v.patternMismatch) return 'Bitte nur Ziffern, Leerzeichen und + ( ) / - verwenden.';
  return `${label}: bitte prüfen Sie Ihre Eingabe.`;
}

function articleFor(name: string): string {
  switch (name) {
    case 'name':
      return 'Ihren Namen';
    case 'email':
      return 'Ihre E-Mail-Adresse';
    case 'nachricht':
      return 'Ihre Nachricht';
    default:
      return 'einen Wert';
  }
}

export function initContactForm(): void {
  const form = document.querySelector<HTMLFormElement>('[data-contact-form]');
  if (!form) return;

  const summary = form.querySelector<HTMLElement>('[data-form-summary]');
  const summaryList = form.querySelector<HTMLUListElement>('[data-form-summary-list]');
  const summaryTitle = form.querySelector<HTMLElement>('[data-form-summary-title]');
  const status = form.querySelector<HTMLElement>('[data-form-status]');
  const submit = form.querySelector<HTMLButtonElement>('[data-submit]');
  const submitLabel = form.querySelector<HTMLElement>('[data-submit-label]');
  const tokenInput = form.querySelector<HTMLInputElement>('[data-form-token]');
  const topic = form.querySelector<HTMLSelectElement>('[data-topic-select]');
  const rental = form.querySelector<HTMLFieldSetElement>('[data-rental-fields]');
  const endpoint = form.dataset['endpoint'] ?? form.action;
  const successPath = form.dataset['success'] ?? '/kontakt/danke/';

  // Eigene, barrierefreie Meldungen statt Browser-Blasen.
  form.noValidate = true;

  // 1. Spam-Schutz-Token holen (schlägt still fehl, z. B. im Astro-Dev-Server ohne PHP).
  fetch(`${endpoint}?token=1`, { headers: { Accept: 'application/json' }, credentials: 'same-origin', cache: 'no-store' })
    .then((r) => (r.ok ? r.json() : null))
    .then((data: { token?: string } | null) => {
      if (data?.token && tokenInput) tokenInput.value = data.token;
    })
    .catch(() => undefined);

  // 5. Vorauswahl des Anliegens aus der URL
  const preset = new URLSearchParams(window.location.search).get('anliegen');
  if (topic && preset && formConfig.topics.some((t) => t.value === preset)) topic.value = preset;

  // 4. Zusatzfelder für Mietanfragen
  const syncRental = () => {
    if (rental && topic) rental.hidden = topic.value !== 'vermietung';
  };
  topic?.addEventListener('change', syncRental);
  syncRental();

  const fields = () =>
    Array.from(form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>('input, select, textarea')).filter(
      (el) => el.type !== 'hidden' && !el.closest('.hp'),
    );

  const errorEl = (name: string) => form.querySelector<HTMLElement>(`#${CSS.escape(name)}-error`);

  const setFieldError = (el: HTMLElement & { name: string }, message: string | null) => {
    const err = errorEl(el.name);
    if (message) {
      el.setAttribute('aria-invalid', 'true');
      if (err) {
        err.textContent = message;
        err.hidden = false;
      }
    } else {
      el.removeAttribute('aria-invalid');
      if (err) {
        err.textContent = '';
        err.hidden = true;
      }
    }
  };

  const showSummary = (errors: { id: string; message: string }[], title = 'Bitte prüfen Sie Ihre Angaben') => {
    if (!summary || !summaryList || !summaryTitle) return;
    summaryTitle.textContent = title;
    summaryList.replaceChildren(
      ...errors.map(({ id, message }) => {
        const li = document.createElement('li');
        if (id) {
          const a = document.createElement('a');
          a.href = `#${id}`;
          a.textContent = message;
          a.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById(id)?.focus();
          });
          li.append(a);
        } else {
          li.textContent = message;
        }
        return li;
      }),
    );
    summary.hidden = false;
    summary.focus();
  };

  const hideSummary = () => {
    if (summary) summary.hidden = true;
  };

  // Fehler am Feld erst nach dem ersten Verlassen anzeigen, danach live korrigieren.
  fields().forEach((el) => {
    el.addEventListener('blur', () => {
      if (el.value !== '' || el.dataset['touched']) {
        el.dataset['touched'] = '1';
        setFieldError(el, el.checkValidity() ? null : messageFor(el));
      }
    });
    el.addEventListener('input', () => {
      if (el.getAttribute('aria-invalid') === 'true' && el.checkValidity()) setFieldError(el, null);
    });
  });

  const setBusy = (busy: boolean) => {
    if (submit) submit.disabled = busy;
    if (submitLabel) submitLabel.textContent = busy ? 'Wird gesendet …' : 'Anfrage senden';
    if (status) status.textContent = busy ? 'Ihre Anfrage wird gesendet …' : '';
    form.setAttribute('aria-busy', String(busy));
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // 2. Clientseitige Prüfung (Komfort – der Server prüft erneut)
    const invalid = fields().filter((el) => !el.checkValidity());
    fields().forEach((el) => setFieldError(el, el.checkValidity() ? null : messageFor(el)));
    if (invalid.length > 0) {
      showSummary(invalid.map((el) => ({ id: el.id, message: messageFor(el) })));
      return;
    }
    hideSummary();

    // 3. Versand
    setBusy(true);
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
      });
      const data = (await response.json().catch(() => null)) as ServerResponse | null;

      if (response.ok && data?.ok) {
        window.location.assign(data.redirect ?? successPath);
        return;
      }

      const errors = data?.errors ?? {};
      const list: { id: string; message: string }[] = [];
      for (const [name, message] of Object.entries(errors)) {
        if (!message) continue;
        const el = form.querySelector<HTMLInputElement>(`[name="${CSS.escape(name)}"]`);
        if (el && name !== 'form') {
          setFieldError(el, message);
          list.push({ id: el.id, message });
        } else {
          list.push({ id: '', message });
        }
      }
      if (list.length === 0) {
        list.push({ id: '', message: 'Ihre Anfrage konnte leider nicht gesendet werden. Bitte versuchen Sie es später erneut.' });
      }
      setBusy(false);
      showSummary(list, response.status >= 500 ? 'Senden fehlgeschlagen' : 'Bitte prüfen Sie Ihre Angaben');
    } catch {
      setBusy(false);
      showSummary(
        [{ id: '', message: 'Keine Verbindung zum Server. Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.' }],
        'Senden fehlgeschlagen',
      );
    }
  });
}
