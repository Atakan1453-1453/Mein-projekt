/**
 * Großansicht für die Galerie auf Basis des nativen <dialog>-Elements.
 * - showModal(): Fokus bleibt automatisch im Dialog, Escape schließt.
 * - Pfeiltasten links/rechts blättern.
 * - Nach dem Schließen erhält das zuletzt geöffnete Vorschaubild den Fokus.
 * Ohne JavaScript öffnen die Links einfach die große Bilddatei.
 */
export function initLightbox(): void {
  document.querySelectorAll<HTMLElement>('[data-gallery]').forEach((gallery) => {
    const dialog = gallery.querySelector<HTMLDialogElement>('[data-lightbox]');
    const img = dialog?.querySelector<HTMLImageElement>('[data-lightbox-img]');
    const caption = dialog?.querySelector<HTMLElement>('[data-lightbox-caption]');
    const counter = dialog?.querySelector<HTMLElement>('[data-lightbox-counter]');
    if (!dialog || !img || !caption || !counter || typeof dialog.showModal !== 'function') return;

    const links = Array.from(gallery.querySelectorAll<HTMLAnchorElement>('[data-gallery-index]'));
    let current = 0;
    let opener: HTMLElement | null = null;

    const show = (index: number) => {
      current = (index + links.length) % links.length;
      const link = links[current];
      if (!link) return;
      img.src = link.dataset['full'] ?? link.href;
      img.alt = link.dataset['alt'] ?? '';
      caption.textContent = link.dataset['caption'] ?? '';
      counter.textContent = `${current + 1} / ${links.length}`;
    };

    links.forEach((link, index) => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        opener = link;
        show(index);
        dialog.showModal();
        dialog.querySelector<HTMLButtonElement>('[data-lightbox-close]')?.focus();
      });
    });

    dialog.querySelector('[data-lightbox-prev]')?.addEventListener('click', () => show(current - 1));
    dialog.querySelector('[data-lightbox-next]')?.addEventListener('click', () => show(current + 1));
    dialog.querySelector('[data-lightbox-close]')?.addEventListener('click', () => dialog.close());

    dialog.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') show(current - 1);
      if (event.key === 'ArrowRight') show(current + 1);
    });

    // Klick auf den abgedunkelten Hintergrund schließt die Großansicht.
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });

    dialog.addEventListener('close', () => opener?.focus());
  });
}
