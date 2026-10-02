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

  locus.querySelectorAll('.lens-panel').forEach(panel => {
    const controls = [...panel.querySelectorAll('.locus-controls [data-locus-focus]')];
    const triggers = [...panel.querySelectorAll('[data-locus-focus]')];
    const features = [...panel.querySelectorAll('[data-locus-feature]')];
    const caption = panel.querySelector('.locus-caption');

    function selectFeature(button) {
      const target = button.dataset.locusFocus;
      triggers.forEach(control => {
        const selected = control.dataset.locusFocus === target;
        control.classList.toggle('is-active', selected);
        control.setAttribute('aria-pressed', String(selected));
      });
      features.forEach(feature => {
        const matches = feature.dataset.locusFeature.split(/\s+/).includes(target);
        feature.classList.toggle('is-emphasized', matches);
      });
      const textControl = controls.find(control => control.dataset.locusFocus === target);
      if (caption && textControl) caption.textContent = textControl.dataset.locusCaption;
    }

    triggers.forEach(button => {
      button.addEventListener('click', () => selectFeature(button));
      if (button.getAttribute('role') !== 'button') return;
      button.addEventListener('keydown', event => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        selectFeature(button);
      });
    });
    const selected = controls.find(button => button.getAttribute('aria-pressed') === 'true');
    if (selected) selectFeature(selected);
  });
});
