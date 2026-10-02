(() => {
  'use strict';

  document.querySelectorAll('[data-track-demo]').forEach(demo => {
    const list = demo.querySelector('[data-demo-list]');
    const initialTracks = Array.from(list.querySelectorAll('[data-demo-track]'));
    const filter = demo.querySelector('[data-demo-filter]');
    const up = demo.querySelector('[data-demo-up]');
    const down = demo.querySelector('[data-demo-down]');
    const count = demo.querySelector('[data-demo-count]');
    const status = demo.querySelector('[data-demo-status]');
    const empty = demo.querySelector('[data-demo-empty]');
    const selected = track => track.querySelector('[data-demo-select]').checked;
    const tracks = () => Array.from(list.children);

    function update(message) {
      const term = filter.value.trim().toLowerCase();
      const ordered = tracks();
      let shown = 0;
      let chosen = 0;
      ordered.forEach(track => {
        track.hidden = !track.dataset.trackName.toLowerCase().includes(term);
        track.classList.toggle('is-selected', selected(track));
        if (!track.hidden) shown += 1;
        if (selected(track)) chosen += 1;
      });
      count.textContent = `${chosen} / ${ordered.length} selected`;
      up.disabled = down.disabled = chosen === 0;
      empty.hidden = shown > 0;
      status.textContent = message || `${chosen} of ${ordered.length} tracks selected. ${shown} shown${term ? '; filtering keeps your selection' : ''}.`;
    }

    function move(direction) {
      const ordered = tracks();
      const moving = ordered.filter(selected);
      if (!moving.length) return;
      const remaining = ordered.filter(track => !selected(track));
      const edge = direction === 'up' ? ordered.indexOf(moving[0]) : ordered.indexOf(moving.at(-1));
      const beforeEdge = ordered.slice(0, edge).filter(track => !selected(track)).length;
      const insertion = Math.max(0, Math.min(remaining.length, beforeEdge + (direction === 'up' ? -1 : 1)));
      const next = [...remaining.slice(0, insertion), ...moving, ...remaining.slice(insertion)];
      if (next.every((track, index) => track === ordered[index])) {
        update(`The selected group is already at the ${direction === 'up' ? 'top' : 'bottom'}.`);
        return;
      }
      // Move the existing nodes, retaining checkbox state and the original
      // relative order within the selected group and the remaining tracks.
      list.append(...next);
      update(`Moved ${moving.length} selected ${moving.length === 1 ? 'track' : 'tracks'} ${direction} as a group. Their order is preserved.`);
    }

    list.addEventListener('change', update.bind(null, null));
    filter.addEventListener('input', update.bind(null, null));
    up.addEventListener('click', () => move('up'));
    down.addEventListener('click', () => move('down'));
    demo.querySelector('[data-demo-reset]').addEventListener('click', () => {
      initialTracks.forEach(track => { track.querySelector('[data-demo-select]').checked = false; });
      list.append(...initialTracks);
      filter.value = '';
      update('Reset: the original track order is restored and the selection is cleared.');
    });
    update('Choose one or more tracks to try the workflow.');
  });
})();
