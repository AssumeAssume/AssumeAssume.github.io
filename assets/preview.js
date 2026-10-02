const names = { a: 'A · 经典学术', b: 'B · 极简现代', c: 'C · 研究作品集' };
const frame = document.getElementById('live-frame');
document.querySelectorAll('.mini-preview').forEach(container => {
  new ResizeObserver(entries => {
    const scale = entries[0].contentRect.width / 1120;
    container.querySelector('iframe').style.transform = `scale(${scale})`;
    container.style.height = `${Math.min(scale * 730, 350)}px`;
  }).observe(container);
});
document.querySelectorAll('[data-theme]').forEach(button => {
  button.addEventListener('click', () => {
    const theme = button.dataset.theme;
    document.querySelectorAll('[data-theme]').forEach(item => {
      item.setAttribute('aria-pressed', String(item === button));
    });
    frame.src = `${theme}/`;
    frame.title = `${names[theme]}学术网站`;
    document.getElementById('preview-title').textContent = names[theme];
    document.getElementById('open-preview').href = `${theme}/`;
    document.querySelector('.live-preview').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
document.querySelectorAll('[data-viewport]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('[data-viewport]').forEach(item => {
      item.setAttribute('aria-pressed', String(item === button));
    });
    frame.classList.toggle('mobile-preview', button.dataset.viewport === 'mobile');
  });
});
