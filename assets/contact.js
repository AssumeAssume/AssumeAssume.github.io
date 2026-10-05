(() => {
  'use strict';

  const pattern = /^[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}$/;

  document.querySelectorAll('[data-email-user][data-email-domain]').forEach((button) => {
    let user;
    let domain;
    try {
      user = atob(button.dataset.emailUser);
      domain = atob(button.dataset.emailDomain);
    } catch {
      return; // The readable address remains available if decoding fails.
    }
    const address = `${user}@${domain}`;
    if (!pattern.test(address)) return;

    button.addEventListener('click', () => {
      window.location.href = `mailto:${encodeURIComponent(user)}@${domain}`;
    });

    // Static HTML only carries the "[at]" form; show the real address once scripts run.
    const contact = button.closest('.email-contact');
    const fallback = contact && contact.querySelector('.email-fallback');
    if (fallback) fallback.textContent = address;
    if (!contact || !navigator.clipboard || !window.isSecureContext) return;

    const copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'email-copy';
    copy.textContent = 'Copy';
    copy.setAttribute('aria-label', 'Copy email address');
    const status = document.createElement('span');
    status.className = 'visually-hidden';
    status.setAttribute('role', 'status');
    let reset;
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(address);
        copy.textContent = 'Copied';
        status.textContent = 'Email address copied';
      } catch {
        copy.textContent = 'Copy failed';
        status.textContent = 'Could not copy the email address';
      }
      clearTimeout(reset);
      reset = setTimeout(() => {
        copy.textContent = 'Copy';
        status.textContent = '';
      }, 2000);
    });
    contact.append(copy, status);
  });
})();
