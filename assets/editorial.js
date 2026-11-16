document.querySelectorAll('.research-locus').forEach(locus => {
  const tabs = [...locus.querySelectorAll('[data-lens]')];

  function selectLens(tab, moveFocus = false) {
    tabs.forEach(item => {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById(item.getAttribute('aria-controls'));
      if (panel) panel.hidden = !selected;
    });
    if (moveFocus) tab.focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectLens(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      let next = index;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      selectLens(tabs[next], true);
    });
  });

  // Each figure explains itself: choosing one of its parts highlights it and shows its caption.
  locus.querySelectorAll('.lens-panel').forEach(panel => {
    const parts = [...panel.querySelectorAll('[data-locus-focus]')];
    const features = [...panel.querySelectorAll('[data-locus-feature]')];
    const caption = panel.querySelector('.locus-caption');

    function selectPart(part) {
      const target = part.dataset.locusFocus;
      parts.forEach(item => {
        item.classList.toggle('is-active', item === part);
        item.setAttribute('aria-pressed', String(item === part));
      });
      features.forEach(feature => {
        const matches = feature.dataset.locusFeature.split(/\s+/).includes(target);
        feature.classList.toggle('is-emphasized', matches);
      });
      // Rewriting unchanged text would make screen readers announce the caption again.
      if (caption && caption.textContent !== part.dataset.locusCaption) caption.textContent = part.dataset.locusCaption;
    }

    parts.forEach(part => {
      part.addEventListener('click', () => selectPart(part));
      part.addEventListener('keydown', event => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        selectPart(part);
      });
    });
    // The markup marks one part as chosen; this also highlights what connects to it.
    const chosen = parts.find(part => part.getAttribute('aria-pressed') === 'true');
    if (chosen) selectPart(chosen);
  });
});
