const dashboard = window.cubatronDashboard;
const state = dashboard.state;
const { escapeHtml, formatRelativeTime, applyThemePreferences } = dashboard.utils;
const { apiGet, apiPost } = dashboard.api;

async function loadFavoriteMixOptions(selectedValue = '') {
  const selectEl = document.getElementById('edit-mix');
  if (!selectEl) return;
  try {
    const recipes = await apiGet('/api/drinks/recipes');
    const options = ['<option value="">-- Sin favorita --</option>'];
    (recipes || []).forEach(r => {
      const name = escapeHtml(r.name || '');
      if (!name) return;
      options.push(`<option value="${name}">${name}</option>`);
    });
    selectEl.innerHTML = options.join('');

    if (selectedValue) {
      const available = Array.from(selectEl.options).some(o => o.value === selectedValue);
      selectEl.value = available ? selectedValue : '';
    } else {
      selectEl.value = '';
    }
  } catch (_) {
    selectEl.innerHTML = '<option value="">-- Sin favorita --</option>';
  }
}

async function loadProfile() {
  state.currentUser = await apiGet('/api/users/me');
  document.getElementById('sb-name').innerText = state.currentUser.full_name || state.currentUser.username;
  document.getElementById('sb-info').innerText = (state.currentUser.info || '').trim() || '\u00a0';
  document.getElementById('sb-level').innerText = 'LVL ' + state.currentUser.level;

  const xpCurrent = state.currentUser.xp % 100;
  document.getElementById('sb-xp').innerText = `${xpCurrent} / 100`;
  document.getElementById('sb-xp-bar').style.width = `${xpCurrent}%`;

  if (state.currentUser.avatar_url) {
    const img = `<img src="${state.currentUser.avatar_url}" class="avatar-img">`;
    document.getElementById('sb-avatar').innerHTML = img;
    document.getElementById('edit-avatar-preview').innerHTML = img;
  }

  document.getElementById('edit-fullname').value = state.currentUser.full_name || '';
  document.getElementById('edit-info').value = state.currentUser.info || '';
  await loadFavoriteMixOptions(state.currentUser.favorite_mix || '');
  document.getElementById('ui-theme').value = state.currentUser.theme_mode || 'dark';
  document.getElementById('ui-accent').value = state.currentUser.accent_color || 'emerald';
  applyThemePreferences(state.currentUser.theme_mode || 'dark', state.currentUser.accent_color || 'emerald');
  const adminNav = document.getElementById('nav-admin');
  if (adminNav) {
    adminNav.classList.toggle('hidden', state.currentUser.role !== 'admin');
  }
}

async function updateProfile(ev) {
  ev.preventDefault();
  const formData = new FormData();
  formData.append('full_name', document.getElementById('edit-fullname').value);
  formData.append('favorite_mix', document.getElementById('edit-mix').value);
  formData.append('info', document.getElementById('edit-info').value);
  formData.append('theme_mode', document.getElementById('ui-theme').value);
  formData.append('accent_color', document.getElementById('ui-accent').value);

  const fileInput = document.getElementById('edit-avatar');
  if (fileInput.files.length > 0) formData.append('avatar', fileInput.files[0]);

  try {
    const response = await fetch('/api/users/me/update', {
      method: 'POST',
      headers: { Authorization: `Bearer ${dashboard.api.getToken()}` },
      body: formData,
    });
    let payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }
    if (!response.ok) {
      const detail = payload?.detail || payload?.message || 'Error actualizando perfil';
      alert(detail);
      return;
    }
    alert(payload?.message || 'Perfil actualizado');
    loadProfile();
  } catch (error) {
    alert('Error actualizando perfil');
  }
}

async function updatePassword(ev) {
  ev.preventDefault();
  const pwd = document.getElementById('edit-password').value;
  try {
    await apiPost('/api/users/me/password', { new_password: pwd });
    alert('Contraseña actualizada con éxito');
    ev.target.reset();
  } catch (e) {
    alert('Error actualizando contraseña');
  }
}

function renderHistoryCards(items, showUser = false) {
  return items.map(h => `
    <div class="history-item">
      <div class="history-user">
        ${h.avatar_url
          ? `<img src="${escapeHtml(h.avatar_url)}" class="history-avatar" alt="avatar">`
          : '<div class="history-avatar-fallback">U</div>'}
        <div class="history-main">
          <span class="history-title">${escapeHtml(h.name)}</span>
          ${showUser ? `<div class="history-time">${escapeHtml(h.full_name || h.username || 'Usuario')}</div>` : ''}
          <div class="history-time">Vaso: ${escapeHtml(h.glass_type || '-')} · Modo: ${escapeHtml(h.serving_mode || '-')}</div>
          ${h.time ? `<div class="history-time" title="${escapeHtml(h.time)}">${escapeHtml(formatRelativeTime(h.time))}</div>` : ''}
        </div>
      </div>
      <div class="history-side">
        <span class="history-completed">Completado</span>
        <span class="history-xp">+${Number(h.xp || 0)} XP</span>
      </div>
    </div>
  `).join('');
}

function updateHistoryPager(labelId, historyState, payload) {
  const page = Number(payload?.page || historyState.page || 1);
  const totalPages = Number(payload?.total_pages || 0);
  const safeTotalPages = totalPages > 0 ? totalPages : 1;
  const label = document.getElementById(labelId);
  if (label) label.innerText = `Página ${page} / ${safeTotalPages}`;
  historyState.page = page;
}

async function loadGlobalHistory(resetPage = false) {
  try {
    if (resetPage) state.globalHistoryState.page = 1;
    const query = new URLSearchParams({
      scope: 'all',
      page: String(state.globalHistoryState.page),
      page_size: String(state.globalHistoryState.pageSize),
      q: state.globalHistoryState.q,
    });
    const payload = await apiGet(`/api/users/history?${query.toString()}`);
    const list = document.getElementById('global-history-list');
    const items = payload?.items || [];
    if (!list) return;
    if (items.length === 0) {
      list.innerHTML = '<p class="muted">No hay consumiciones registradas.</p>';
      updateHistoryPager('global-history-page', state.globalHistoryState, payload);
      return;
    }
    list.innerHTML = renderHistoryCards(items, true);
    updateHistoryPager('global-history-page', state.globalHistoryState, payload);
  } catch (e) {
    console.error('Error cargando historial global', e);
  }
}

async function loadMyHistory(resetPage = false) {
  try {
    if (resetPage) state.myHistoryState.page = 1;
    const query = new URLSearchParams({
      scope: 'me',
      page: String(state.myHistoryState.page),
      page_size: String(state.myHistoryState.pageSize),
      q: state.myHistoryState.q,
    });
    const payload = await apiGet(`/api/users/history?${query.toString()}`);
    const list = document.getElementById('my-history-list');
    const items = payload?.items || [];
    if (!list) return;
    if (items.length === 0) {
      list.innerHTML = '<p class="muted">Aún no has preparado nada.</p>';
      updateHistoryPager('my-history-page', state.myHistoryState, payload);
      return;
    }
    list.innerHTML = renderHistoryCards(items, false);
    updateHistoryPager('my-history-page', state.myHistoryState, payload);
  } catch (e) {
    console.error('Error cargando historial personal', e);
  }
}

function applyGlobalHistoryFilter() {
  state.globalHistoryState.q = (document.getElementById('global-history-filter')?.value || '').trim();
  loadGlobalHistory(true);
}

function changeGlobalHistoryPage(delta) {
  const nextPage = Math.max(1, Number(state.globalHistoryState.page) + Number(delta || 0));
  if (nextPage === state.globalHistoryState.page) return;
  state.globalHistoryState.page = nextPage;
  loadGlobalHistory();
}

function applyMyHistoryFilter() {
  state.myHistoryState.q = (document.getElementById('my-history-filter')?.value || '').trim();
  loadMyHistory(true);
}

function changeMyHistoryPage(delta) {
  const nextPage = Math.max(1, Number(state.myHistoryState.page) + Number(delta || 0));
  if (nextPage === state.myHistoryState.page) return;
  state.myHistoryState.page = nextPage;
  loadMyHistory();
}

Object.assign(window, {
  loadFavoriteMixOptions,
  loadProfile,
  updateProfile,
  updatePassword,
  renderHistoryCards,
  updateHistoryPager,
  loadGlobalHistory,
  loadMyHistory,
  applyGlobalHistoryFilter,
  changeGlobalHistoryPage,
  applyMyHistoryFilter,
  changeMyHistoryPage,
});
