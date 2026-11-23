/**
 * Mobiles Menü: Auf-/Zuklappen per Button, Escape schließt, Fokus kehrt
 * zum Button zurück. Ohne JavaScript (oder in Browsern ohne
 * `@media (scripting)`) bleibt die Navigation dauerhaft sichtbar.
 */
const DESKTOP_QUERY = '(min-width: 64rem)';

export function initNavigation(): void {
  const header = document.querySelector<HTMLElement>('[data-site-header]');
  const toggle = header?.querySelector<HTMLButtonElement>('[data-nav-toggle]');
  const nav = header?.querySelector<HTMLElement>('[data-nav]');
  if (!header || !toggle || !nav) return;

  // Nur aktivieren, wenn das CSS die mobile Einklapp-Variante auch anwendet.
  if (!window.matchMedia('(scripting: enabled)').matches) return;

  toggle.hidden = false;
  const desktop = window.matchMedia(DESKTOP_QUERY);

  const setOpen = (open: boolean, { returnFocus = false } = {}) => {
    toggle.setAttribute('aria-expanded', String(open));
    header.toggleAttribute('data-open', open);
    if (!open && returnFocus) toggle.focus();
  };

  toggle.addEventListener('click', () => {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });

  header.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && header.hasAttribute('data-open')) {
      setOpen(false, { returnFocus: true });
    }
  });

  // Link geklickt (z. B. Sprungmarke auf derselben Seite) → Menü schließen.
  nav.addEventListener('click', (event) => {
    if ((event.target as HTMLElement).closest('a')) setOpen(false);
  });

  // Beim Wechsel auf Desktop-Breite Zustand zurücksetzen.
  desktop.addEventListener('change', (event) => {
    if (event.matches) setOpen(false);
  });
}
