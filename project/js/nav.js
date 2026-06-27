// Nav integration — runs after bundle unpacks, updates nav with real user state

(async function () {
  await new Promise(r => {
    if (document.readyState !== 'loading') return r();
    document.addEventListener('DOMContentLoaded', r, { once: true });
  });

  const session = await JamSpot.getSession();

  // Patch all "Log in" / "Sign up" links to point to auth page
  document.querySelectorAll('a[href="#login"], a[href="#signup"], a[href="#auth"]').forEach(a => {
    a.href = '/auth.html';
  });

  // If user is logged in, update any visible display-name / avatar elements
  if (session.authenticated) {
    // Replace "Log in" text nodes in nav menus with user name
    document.querySelectorAll('[data-nav-login]').forEach(el => {
      el.textContent = session.name || session.email || 'Account';
    });

    // Show host dashboard link if user is host
    if (session.role === 'host') {
      document.querySelectorAll('[data-nav-host-only]').forEach(el => {
        el.style.display = '';
      });
    }
  }

  // Wire logout buttons
  document.querySelectorAll('[data-action="logout"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      await JamSpot.apiFetch('/api/auth/logout', { method: 'POST' });
      JamSpot.session = null;
      window.location.href = '/';
    });
  });
})();
