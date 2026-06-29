// Jamspot page integrations — wires each page to the backend API

(async function () {
  await new Promise(r => {
    if (document.readyState !== 'loading') return r();
    document.addEventListener('DOMContentLoaded', r, { once: true });
  });

  const page = window.location.pathname.replace(/^\//, '') || 'index.html';

  // ─── Fix bundle links (Claude Design exports use "Stays X.html" filenames) ─────────────
  const ROUTE_MAP = {
    'Stays Homepage.html': '/',
    'Stays Auth.html': '/auth.html',
    'Stays Listing.html': '/listing.html',
    'Stays Host.html': '/host.html',
    'Stays Trips.html': '/trips.html',
    'Stays Wishlists.html': '/wishlists.html',
    'Stays Messages.html': '/messages.html',
    'Stays Profile.html': '/profile.html',
    'Stays Help.html': '/help.html',
    'Stays Experiences.html': '/experiences.html',
    'Stays Services.html': '/services.html',
    'Stays Search.html': '/search.html',
    'Stays Checkout.html': '/checkout.html',
    'Stays Host Dashboard.html': '/host-dashboard.html',
  };
  document.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    if (ROUTE_MAP[href] !== undefined) a.setAttribute('href', ROUTE_MAP[href]);
  });

  // ─── Helpers ───────────────────────────────────────────────────────────────────────────

  function formatPrice(n) { return '$' + Number(n || 0).toFixed(0); }
  function stars(avg) { return '★'.repeat(Math.round(avg || 0)) + '☆'.repeat(5 - Math.round(avg || 0)); }
  function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

  function cardHTML(listing) {
    const img = (listing.photos || [])[0] || '';
    const city = (listing.location || {}).city || '';
    const price = listing.price || listing.pricePerNight || 0;
    const rating = (listing.ratings || {}).average || 0;
    return `
      <a href="/listing.html?id=${esc(listing.id)}&type=${esc(listing.listingType || 'listing')}" class="card" style="text-decoration:none;color:inherit;display:block;">
        <div class="card-img" style="aspect-ratio:1;border-radius:12px;overflow:hidden;background:#eee;margin-bottom:8px;">
          ${img ? `<img src="${esc(img)}" style="width:100%;height:100%;object-fit:cover;" loading="lazy">` : ''}
        </div>
        <div style="font-weight:600;font-size:14px;">${esc(listing.title)}</div>
        ${city ? `<div style="color:#717171;font-size:13px;">${esc(city)}</div>` : ''}
        <div style="font-size:13px;margin-top:2px;">${formatPrice(price)}<span style="color:#717171;"> / night</span>
          ${rating ? ` · <span style="color:#222;">★ ${Number(rating).toFixed(1)}</span>` : ''}
        </div>
      </a>`;
  }

  function showToast(msg, ok = true) {
    const t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = `position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:${ok ? '#222' : '#c0392b'};color:#fff;padding:10px 20px;border-radius:8px;z-index:99999;font-size:14px;`;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
  }

  // ─── Homepage (index.html) ───────────────────────────────────────────────────────────────────────
  if (page === '' || page === 'index.html') {
    const grid = document.querySelector('.grid');
    if (grid) {
      try {
        const data = await JamSpot.apiFetch('/api/listings');
        const listings = data.listings || [];
        if (listings.length) {
          grid.innerHTML = listings.map(cardHTML).join('');
        }
      } catch (e) { console.warn('Homepage listings error', e); }
    }

    // Wire search form submission
    const searchForm = document.querySelector('form.search, .searchcard form, form[role="search"]');
    if (searchForm) {
      searchForm.addEventListener('submit', e => {
        e.preventDefault();
        const q = (searchForm.querySelector('input[type="text"], input[type="search"]') || {}).value || '';
        window.location.href = `/search.html?q=${encodeURIComponent(q)}`;
      });
    }

    // Category bar
    document.querySelectorAll('.catbar button, [data-category]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const cat = btn.dataset.category || btn.textContent.trim().toLowerCase();
        try {
          const data = await JamSpot.apiFetch(`/api/listings?category=${encodeURIComponent(cat)}`);
          if (grid) grid.innerHTML = (data.listings || []).map(cardHTML).join('');
        } catch (e) { console.warn('Category filter error', e); }
      });
    });
  }

  // ─── Search ───────────────────────────────────────────────────────────────────────────
  if (page === 'search.html') {
    const q = JamSpot.getParam('q');
    const type = JamSpot.getParam('type') || 'all';
    const grid = document.querySelector('.grid, .results-grid, [data-results]');
    if (grid) {
      try {
        const data = await JamSpot.apiFetch(`/api/search?q=${encodeURIComponent(q)}&type=${encodeURIComponent(type)}`);
        const all = [...(data.listings || []), ...(data.experiences || []), ...(data.services || [])];
        grid.innerHTML = all.length ? all.map(cardHTML).join('') : '<p style="padding:24px;color:#717171;">No results found.</p>';
      } catch (e) { console.warn('Search error', e); }
    }
  }

  // ─── Listing Detail ────────────────────────────────────────────────────────────────────────
  if (page === 'listing.html') {
    const id = JamSpot.getParam('id');
    const type = JamSpot.getParam('type') || 'listing';
    if (!id) return;

    const endpoint = type === 'experience' ? `/api/experiences/${id}` : type === 'service' ? `/api/services/${id}` : `/api/listings/${id}`;

    try {
      const listing = await JamSpot.apiFetch(endpoint);

      // Populate title
      document.querySelectorAll('.listing-title, [data-listing-title], h1').forEach(el => { el.textContent = listing.title || ''; });

      // Price
      document.querySelectorAll('.price-val, [data-listing-price]').forEach(el => { el.textContent = formatPrice(listing.price); });

      // Description
      document.querySelectorAll('.listing-desc, [data-listing-desc]').forEach(el => { el.textContent = listing.description || ''; });

      // Amenities
      const amenitiesEl = document.querySelector('.amenities-list, [data-amenities]');
      if (amenitiesEl && listing.amenities) {
        amenitiesEl.innerHTML = listing.amenities.map(a => `<div class="amenity">${esc(a)}</div>`).join('');
      }

      // Reserve button → checkout
      document.querySelectorAll('[data-action="reserve"], .book-btn, button.reserve').forEach(btn => {
        btn.addEventListener('click', () => {
          const checkin = document.querySelector('[data-checkin]')?.value || '';
          const checkout = document.querySelector('[data-checkout]')?.value || '';
          const guests = document.querySelector('[data-guests]')?.value || '1';
          window.location.href = `/checkout.html?listingId=${id}&type=${type}&checkin=${checkin}&checkout=${checkout}&guests=${guests}`;
        });
      });

      // Reviews
      const reviewsData = await JamSpot.apiFetch(`/api/reviews?listingId=${id}&listingType=${type}`).catch(() => ({ reviews: [] }));
      const reviewsEl = document.querySelector('.reviews-list, [data-reviews]');
      if (reviewsEl && reviewsData.reviews.length) {
        reviewsEl.innerHTML = reviewsData.reviews.map(r => `
          <div class="review" style="padding:16px 0;border-top:1px solid #eee;">
            <div style="font-size:13px;color:#222;">★ ${Number(r.rating).toFixed(1)}</div>
            <div style="font-size:14px;margin-top:4px;">${esc(r.comment)}</div>
          </div>`).join('');
      }

      // Map embed
      const loc = listing.location || {};
      const mapContainer = document.querySelector('[data-map], .listing-map, #listing-map');
      if (mapContainer && (loc.lat || loc.address || listing.title)) {
        const q = encodeURIComponent(loc.address || `${listing.title} ${loc.city || ''}`);
        mapContainer.innerHTML = `<iframe title="Location map" width="100%" height="300" style="border:0;border-radius:12px;" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://maps.google.com/maps?q=${q}&output=embed"></iframe>`;
      }

      // Wishlist heart
      document.querySelectorAll('[data-action="wishlist"]').forEach(btn => {
        btn.addEventListener('click', async () => {
          try {
            const session = await JamSpot.getSession();
            if (!session.authenticated) { window.location.href = '/auth.html'; return; }
            let wishlists = (await JamSpot.apiFetch('/api/wishlists')).wishlists || [];
            if (!wishlists.length) {
              const wl = await JamSpot.apiFetch('/api/wishlists', { method: 'POST', body: { name: 'Saved places' } });
              wishlists = [wl];
            }
            await JamSpot.apiFetch(`/api/wishlists/${wishlists[0].id}/add`, { method: 'POST', body: { listingId: id } });
            showToast('Saved to wishlist');
          } catch (e) { showToast(e.message || 'Error saving', false); }
        });
      });

    } catch (e) { console.error('Listing detail error', e); }
  }

  // ─── Checkout ───────────────────────────────────────────────────────────────────────────
  if (page === 'checkout.html') {
    const listingId = JamSpot.getParam('listingId');
    const type = JamSpot.getParam('type') || 'listing';
    const checkin = JamSpot.getParam('checkin');
    const checkout = JamSpot.getParam('checkout');
    const guests = JamSpot.getParam('guests') || '1';

    if (listingId) {
      const endpoint = type === 'experience' ? `/api/experiences/${listingId}` : `/api/listings/${listingId}`;
      const listing = await JamSpot.apiFetch(endpoint).catch(() => null);
      if (listing) {
        document.querySelectorAll('[data-listing-title], .checkout-title').forEach(el => { el.textContent = listing.title; });
        document.querySelectorAll('[data-listing-price], .price-val').forEach(el => { el.textContent = formatPrice(listing.price); });
      }

      // Pre-fill date/guest fields if present in URL
      if (checkin) document.querySelectorAll('[name="checkin"], [data-checkin]').forEach(el => { el.value = checkin; });
      if (checkout) document.querySelectorAll('[name="checkout"], [data-checkout]').forEach(el => { el.value = checkout; });
      if (guests) document.querySelectorAll('[name="guests"], [data-guests]').forEach(el => { el.value = guests; });

      document.querySelectorAll('[data-action="confirm-booking"], .reserve-btn, button[type="submit"]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.preventDefault();
          const session = await JamSpot.getSession();
          if (!session.authenticated) { window.location.href = '/auth.html'; return; }
          try {
            const res = await JamSpot.apiFetch('/api/bookings', {
              method: 'POST',
              body: { listing_id: listingId, listing_type: type, check_in: checkin, check_out: checkout, guests: parseInt(guests) || 1 },
            });
            showToast('Booking confirmed! ' + (res.confirmation_code || ''));
            setTimeout(() => { window.location.href = '/trips.html'; }, 1500);
          } catch (err) { showToast(err.message || 'Booking failed', false); }
        });
      });
    }
  }

  // ─── Auth ──────────────────────────────────────────────────────────────────────────
  if (page === 'auth.html') {
    // Redirect if already logged in
    const s = await JamSpot.getSession();
    if (s.authenticated) { window.location.href = '/'; return; }

    async function handleAuth(e) {
      e.preventDefault();
      const form = e.target.closest('form') || e.target;
      const email = (form.querySelector('[name="email"], input[type="email"]') || {}).value || '';
      const password = (form.querySelector('[name="password"], input[type="password"]') || {}).value || '';
      const name = (form.querySelector('[name="name"], [name="full_name"]') || {}).value || '';
      const isLogin = !name;
      try {
        if (isLogin) {
          await JamSpot.apiFetch('/api/auth/login', { method: 'POST', body: { email, password } });
        } else {
          await JamSpot.apiFetch('/api/auth/register', { method: 'POST', body: { email, password, name } });
        }
        window.location.href = '/';
      } catch (err) { showToast(err.message || 'Auth failed', false); }
    }

    document.querySelectorAll('form, [data-action="login"], [data-action="signup"]').forEach(el => {
      el.addEventListener('submit', handleAuth);
    });
    document.querySelectorAll('button[type="submit"], .auth-btn').forEach(btn => {
      btn.addEventListener('click', handleAuth);
    });
  }

  // ─── Trips ────────────────────────────────────────────────────────────────────────────
  if (page === 'trips.html') {
    await JamSpot.requireAuth();
    try {
      const data = await JamSpot.apiFetch('/api/bookings/my');
      const bookings = data.bookings || [];
      const now = new Date().toISOString().slice(0, 10);

      const upcoming = bookings.filter(b => b.checkOut >= now && b.status !== 'cancelled');
      const past = bookings.filter(b => b.checkOut < now || b.status === 'cancelled');

      function tripHTML(b) {
        return `<div class="trip" data-booking-id="${esc(b.id)}" style="padding:16px;border:1px solid #eee;border-radius:12px;margin-bottom:12px;">
          <div style="font-weight:600;">${esc(b.listingId)}</div>
          <div style="color:#717171;font-size:13px;">${esc(b.checkIn)} → ${esc(b.checkOut)} · ${b.guests} guest${b.guests > 1 ? 's' : ''}</div>
          <div style="font-size:13px;margin-top:4px;">Status: <strong>${esc(b.status)}</strong> · ${formatPrice(b.totalPrice)}</div>
          ${b.status === 'pending' || b.status === 'confirmed' ? `<button data-action="cancel-booking" data-id="${esc(b.id)}" style="margin-top:8px;padding:6px 12px;border:1px solid #ccc;border-radius:6px;cursor:pointer;font-size:13px;">Cancel</button>` : ''}
        </div>`;
      }

      const upcomingEl = document.querySelector('[data-tab="upcoming"], .trips-upcoming');
      const pastEl = document.querySelector('[data-tab="past"], .trips-past');
      if (upcomingEl) upcomingEl.innerHTML = upcoming.length ? upcoming.map(tripHTML).join('') : '<p style="color:#717171;padding:16px;">No upcoming trips.</p>';
      if (pastEl) pastEl.innerHTML = past.length ? past.map(tripHTML).join('') : '<p style="color:#717171;padding:16px;">No past trips.</p>';

      document.addEventListener('click', async e => {
        if (e.target.dataset.action === 'cancel-booking') {
          const id = e.target.dataset.id;
          try {
            await JamSpot.apiFetch(`/api/bookings/${id}/cancel`, { method: 'POST' });
            showToast('Booking cancelled');
            e.target.closest('[data-booking-id]').querySelector('strong').textContent = 'cancelled';
            e.target.remove();
          } catch (err) { showToast(err.message, false); }
        }
      });
    } catch (e) { console.error('Trips error', e); }
  }

  // ─── Messages ────────────────────────────────────────────────────────────────────────────
  if (page === 'messages.html') {
    await JamSpot.requireAuth();
    const listEl = document.querySelector('.convlist, .inbox-list, [data-convlist]');
    const threadEl = document.querySelector('.inbox-thread, .messages-thread, [data-thread]');

    async function loadConversations() {
      try {
        const data = await JamSpot.apiFetch('/api/conversations');
        const convs = data.conversations || [];
        if (!listEl) return;
        listEl.innerHTML = convs.length ? convs.map(c => `
          <div class="conv-item" data-conv-id="${esc(c.id)}" style="padding:16px;cursor:pointer;border-bottom:1px solid #f0f0f0;">
            <div style="font-weight:600;font-size:14px;">${esc(c.listingId || 'Conversation')}</div>
            <div style="color:#717171;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${esc(c.lastMessage || '')}</div>
          </div>`).join('') : '<p style="padding:16px;color:#717171;">No messages yet.</p>';

        listEl.querySelectorAll('[data-conv-id]').forEach(item => {
          item.addEventListener('click', () => loadThread(item.dataset.convId));
        });
      } catch (e) { console.error('Conversations error', e); }
    }

    async function loadThread(convId) {
      if (!threadEl) return;
      await JamSpot.apiFetch(`/api/conversations/${convId}/read`, { method: 'PUT' }).catch(() => {});
      const data = await JamSpot.apiFetch(`/api/conversations/${convId}`);
      const msgs = data.messages || [];
      const session = await JamSpot.getSession();

      threadEl.innerHTML = msgs.map(m => {
        const mine = m.senderId === session.uid;
        return `<div style="display:flex;justify-content:${mine ? 'flex-end' : 'flex-start'};margin:8px 0;">
          <div style="max-width:70%;padding:10px 14px;border-radius:16px;background:${mine ? '#222' : '#f0f0f0'};color:${mine ? '#fff' : '#222'};font-size:14px;">${esc(m.body)}</div>
        </div>`;
      }).join('');

      // Wire send form
      const composer = document.querySelector('.inbox-composer, [data-composer]');
      const input = composer?.querySelector('input, textarea');
      const sendBtn = composer?.querySelector('button');
      if (sendBtn && input) {
        sendBtn.onclick = async () => {
          const body = input.value.trim();
          if (!body) return;
          await JamSpot.apiFetch(`/api/conversations/${convId}/messages`, { method: 'POST', body: { body } });
          input.value = '';
          loadThread(convId);
        };
      }
    }

    await loadConversations();
  }

  // ─── Wishlists ───────────────────────────────────────────────────────────────────────────
  if (page === 'wishlists.html') {
    await JamSpot.requireAuth();
    const container = document.querySelector('.wishlists-grid, [data-wishlists], main');
    try {
      const data = await JamSpot.apiFetch('/api/wishlists');
      const lists = data.wishlists || [];
      if (container) {
        container.innerHTML = lists.length ? lists.map(wl => `
          <div class="wishlist-card" style="padding:16px;border:1px solid #eee;border-radius:12px;margin-bottom:16px;">
            <h3 style="margin-bottom:8px;">${esc(wl.name)}</h3>
            <div style="color:#717171;font-size:13px;">${(wl.listingIds || []).length} saved</div>
          </div>`).join('') : '<p style="padding:24px;color:#717171;">No wishlists yet. Save listings from the listing page.</p>';
      }
    } catch (e) { console.error('Wishlists error', e); }
  }

  // ─── Profile ────────────────────────────────────────────────────────────────────────────
  if (page === 'profile.html') {
    await JamSpot.requireAuth();
    try {
      const profile = await JamSpot.apiFetch('/api/profile');
      document.querySelectorAll('[name="name"], [data-profile-name]').forEach(el => { el.value = profile.name || ''; });
      document.querySelectorAll('[name="email"], [data-profile-email]').forEach(el => { el.value = profile.email || ''; });
      document.querySelectorAll('[name="phone"], [data-profile-phone]').forEach(el => { el.value = profile.phone || ''; });
      document.querySelectorAll('[name="bio"], [data-profile-bio]').forEach(el => { el.value = profile.bio || ''; });

      document.querySelectorAll('[data-action="save-profile"], form').forEach(el => {
        el.addEventListener('submit', async (e) => {
          e.preventDefault();
          const name = document.querySelector('[name="name"]')?.value || '';
          const phone = document.querySelector('[name="phone"]')?.value || '';
          const bio = document.querySelector('[name="bio"]')?.value || '';
          try {
            await JamSpot.apiFetch('/api/profile', { method: 'PUT', body: { name, phone, bio } });
            showToast('Profile saved');
          } catch (err) { showToast(err.message || 'Error saving', false); }
        });
      });
    } catch (e) { console.error('Profile error', e); }
  }

  // ─── Host Dashboard ────────────────────────────────────────────────────────────────────────
  if (page === 'host-dashboard.html') {
    await JamSpot.requireAuth();
    try {
      const [listingsData, earningsData, analyticsData] = await Promise.all([
        JamSpot.apiFetch('/api/listings/host/mine'),
        JamSpot.apiFetch('/api/host/earnings'),
        JamSpot.apiFetch('/api/host/analytics'),
      ]);

      // Earnings summary
      document.querySelectorAll('[data-earnings-total]').forEach(el => { el.textContent = formatPrice(earningsData.totalRevenue); });
      document.querySelectorAll('[data-earnings-pending]').forEach(el => { el.textContent = formatPrice(earningsData.pendingPayout); });

      // Analytics
      document.querySelectorAll('[data-analytics-bookings]').forEach(el => { el.textContent = analyticsData.confirmedBookings || 0; });
      document.querySelectorAll('[data-analytics-rate]').forEach(el => { el.textContent = (analyticsData.bookingRate || 0) + '%'; });

      // Listings
      const listingsEl = document.querySelector('[data-host-listings], .host-listings');
      const listings = listingsData.listings || [];
      if (listingsEl) {
        listingsEl.innerHTML = listings.length ? listings.map(l => `
          <div style="padding:16px;border:1px solid #eee;border-radius:12px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="font-weight:600;">${esc(l.title)}</div>
              <div style="color:#717171;font-size:13px;">${formatPrice(l.price)}/night · ${esc((l.location || {}).city || '')}</div>
            </div>
            <a href="/listing.html?id=${esc(l.id)}" style="font-size:13px;color:#FFB400;">View →</a>
          </div>`).join('') : '<p style="color:#717171;padding:16px;">No listings yet.</p>';
      }

      // Add listing button + create-listing modal
      const addBtn = document.querySelector('[data-action="add-listing"], .add-listing-btn');
      if (addBtn || listingsEl) {
        const modalId = 'js-create-listing-modal';
        if (!document.getElementById(modalId)) {
          const modal = document.createElement('div');
          modal.id = modalId;
          modal.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center;';
          modal.innerHTML = `
            <div style="background:#fff;border-radius:16px;padding:32px;width:min(520px,95vw);max-height:90vh;overflow-y:auto;position:relative;">
              <button id="js-close-modal" style="position:absolute;top:16px;right:16px;border:none;background:none;font-size:22px;cursor:pointer;">✕</button>
              <h2 style="margin:0 0 24px;font-size:20px;font-weight:700;">Add a new listing</h2>
              <form id="js-create-listing-form" style="display:flex;flex-direction:column;gap:14px;">
                <div>
                  <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Title</label>
                  <input name="title" required placeholder="Cozy studio in Brooklyn" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                </div>
                <div>
                  <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Address</label>
                  <input name="address" id="js-address-input" required autocomplete="off" placeholder="Start typing an address…" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                  <div id="js-places-dropdown" style="display:none;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;background:#fff;max-height:180px;overflow-y:auto;"></div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Price / night ($)</label>
                    <input name="price" type="number" min="1" required placeholder="150" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                  </div>
                  <div>
                    <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Category</label>
                    <select name="category" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                      <option value="home">Home</option><option value="studio">Studio</option>
                      <option value="beachfront">Beachfront</option><option value="cabin">Cabin</option>
                      <option value="apartment">Apartment</option><option value="villa">Villa</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Description</label>
                  <textarea name="description" rows="3" placeholder="Tell guests about your space…" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;resize:vertical;box-sizing:border-box;"></textarea>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
                  <div>
                    <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Bedrooms</label>
                    <input name="bedrooms" type="number" min="0" value="1" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                  </div>
                  <div>
                    <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Bathrooms</label>
                    <input name="bathrooms" type="number" min="0" step="0.5" value="1" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                  </div>
                  <div>
                    <label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Max guests</label>
                    <input name="maxGuests" type="number" min="1" value="2" style="width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;box-sizing:border-box;">
                  </div>
                </div>
                <button type="submit" style="margin-top:8px;padding:14px;background:#222;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;">Create listing</button>
              </form>
            </div>`;
          document.body.appendChild(modal);

          // Hidden location fields populated by Places autocomplete
          let selectedLocation = {};

          // Close modal
          document.getElementById('js-close-modal').addEventListener('click', () => { modal.style.display = 'none'; });
          modal.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; });

          // Address autocomplete via backend Places proxy
          const addressInput = document.getElementById('js-address-input');
          const dropdown = document.getElementById('js-places-dropdown');
          let debounceTimer;
          addressInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const q = addressInput.value.trim();
            if (q.length < 3) { dropdown.style.display = 'none'; return; }
            debounceTimer = setTimeout(async () => {
              try {
                const res = await JamSpot.apiFetch(`/api/listings/places/search?q=${encodeURIComponent(q)}`);
                const results = res.results || [];
                if (!results.length) { dropdown.style.display = 'none'; return; }
                dropdown.innerHTML = results.map((r, i) => `
                  <div data-idx="${i}" style="padding:10px 14px;cursor:pointer;font-size:14px;border-bottom:1px solid #f0f0f0;" class="places-opt">
                    ${esc(r.name)}${r.address ? ' — <span style="color:#717171">' + esc(r.address) + '</span>' : ''}
                  </div>`).join('');
                dropdown.style.display = 'block';
                dropdown._results = results;
              } catch { dropdown.style.display = 'none'; }
            }, 350);
          });

          dropdown.addEventListener('click', async e => {
            const opt = e.target.closest('.places-opt');
            if (!opt) return;
            const r = dropdown._results[parseInt(opt.dataset.idx)];
            addressInput.value = r.address || r.name;
            dropdown.style.display = 'none';
            // Fetch full details for lat/lng/city
            try {
              const detail = await JamSpot.apiFetch(`/api/listings/places/${encodeURIComponent(r.placeId || r.place_id || r.id || '')}`);
              selectedLocation = {
                address: detail.address || r.address || r.name,
                city: detail.city || '',
                lat: detail.lat || null,
                lng: detail.lng || null,
              };
            } catch { selectedLocation = { address: r.address || r.name, city: '' }; }
          });

          // Form submit
          document.getElementById('js-create-listing-form').addEventListener('submit', async e => {
            e.preventDefault();
            const fd = new FormData(e.target);
            const body = {
              title: fd.get('title'),
              description: fd.get('description'),
              price: parseFloat(fd.get('price')),
              category: fd.get('category'),
              bedrooms: parseInt(fd.get('bedrooms')),
              bathrooms: parseFloat(fd.get('bathrooms')),
              maxGuests: parseInt(fd.get('maxGuests')),
              location: Object.keys(selectedLocation).length ? selectedLocation : { address: fd.get('address') },
              amenities: [],
            };
            try {
              const submitBtn = e.target.querySelector('[type="submit"]');
              submitBtn.textContent = 'Creating…';
              submitBtn.disabled = true;
              await JamSpot.apiFetch('/api/listings', { method: 'POST', body });
              showToast('Listing created!');
              modal.style.display = 'none';
              // Refresh listings
              const refreshed = await JamSpot.apiFetch('/api/listings/host/mine');
              const newListings = refreshed.listings || [];
              if (listingsEl) listingsEl.innerHTML = newListings.length ? newListings.map(l => `
                <div style="padding:16px;border:1px solid #eee;border-radius:12px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <div style="font-weight:600;">${esc(l.title)}</div>
                    <div style="color:#717171;font-size:13px;">${formatPrice(l.price)}/night · ${esc((l.location || {}).city || '')}</div>
                  </div>
                  <a href="/listing.html?id=${esc(l.id)}" style="font-size:13px;color:#FFB400;">View →</a>
                </div>`).join('') : '<p style="color:#717171;padding:16px;">No listings yet.</p>';
            } catch (err) {
              showToast(err.message || 'Failed to create listing', false);
              const sb = e.target.querySelector('[type="submit"]');
              sb.textContent = 'Create listing'; sb.disabled = false;
            }
          });
        }

        // Wire add-listing button — also inject one if none found
        const openModal = () => { document.getElementById(modalId).style.display = 'flex'; };
        if (addBtn) {
          addBtn.addEventListener('click', e => { e.preventDefault(); openModal(); });
        } else if (listingsEl) {
          const fab = document.createElement('button');
          fab.textContent = '+ Add listing';
          fab.style.cssText = 'margin-bottom:16px;padding:10px 20px;background:#222;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;';
          fab.addEventListener('click', openModal);
          listingsEl.parentElement?.insertBefore(fab, listingsEl);
        }
      }
    } catch (e) { console.error('Host dashboard error', e); }
  }

  // ─── Host onboarding ───────────────────────────────────────────────────────────────────────
  if (page === 'host.html') {
    document.querySelectorAll('[data-action="become-host"], .host-cta button, .cta-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const session = await JamSpot.getSession();
        if (!session.authenticated) { window.location.href = '/auth.html'; return; }
        try {
          await JamSpot.apiFetch('/api/profile', { method: 'PUT', body: { role: 'host' } });
          window.location.href = '/host-dashboard.html';
        } catch (err) { showToast(err.message || 'Error', false); }
      });
    });
  }

  // ─── Experiences ──────────────────────────────────────────────────────────────────────────
  if (page === 'experiences.html') {
    const grid = document.querySelector('.grid, .experiences-grid, [data-grid]');
    if (grid) {
      try {
        const data = await JamSpot.apiFetch('/api/experiences');
        const items = data.experiences || [];
        grid.innerHTML = items.length ? items.map(e => cardHTML({ ...e, listingType: 'experience' })).join('') : '<p style="padding:24px;color:#717171;">No experiences yet.</p>';
      } catch (e) { console.warn('Experiences error', e); }
    }
  }

  // ─── Services ───────────────────────────────────────────────────────────────────────────
  if (page === 'services.html') {
    const grid = document.querySelector('.grid, .services-grid, [data-grid]');
    if (grid) {
      try {
        const data = await JamSpot.apiFetch('/api/services');
        const items = data.services || [];
        grid.innerHTML = items.length ? items.map(s => cardHTML({ ...s, listingType: 'service' })).join('') : '<p style="padding:24px;color:#717171;">No services yet.</p>';
      } catch (e) { console.warn('Services error', e); }
    }
  }

})();
