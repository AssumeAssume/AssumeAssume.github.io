const lensTabs = [...document.querySelectorAll('[data-lens]')];

function selectLens(tab, moveFocus = false) {
  lensTabs.forEach(item => {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
  });
  if (moveFocus) tab.focus();
}

lensTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectLens(tab));
  tab.addEventListener('keydown', event => {
    const keys = ['ArrowRight', 'ArrowLeft', 'Home', 'End'];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    let next = index;
    if (event.key === 'ArrowRight') next = (index + 1) % lensTabs.length;
    if (event.key === 'ArrowLeft') next = (index - 1 + lensTabs.length) % lensTabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = lensTabs.length - 1;
    selectLens(lensTabs[next], true);
  });
});
