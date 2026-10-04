(() => {
  'use strict';

  document.querySelectorAll('[data-email-user][data-email-domain]').forEach((button) => {
    button.addEventListener('click', () => {
      try {
        const user = atob(button.dataset.emailUser);
        const domain = atob(button.dataset.emailDomain);
        const address = `${user}@${domain}`;
        if (!/^[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}$/.test(address)) return;
        window.location.href = `mailto:${encodeURIComponent(user)}@${domain}`;
      } catch {
        // The readable address remains available if decoding fails.
      }
    });
  });
})();
