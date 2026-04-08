const dashboard = window.cubatronDashboard;
const state = dashboard.state;
const { escapeHtml, slugifyGlassKey, normalizeModeMap, formatRelativeTime } = dashboard.utils;
const { apiGet, apiPost, authHeaders } = dashboard.api;

function getAdminGlassSource() {
  return state.adminGlassesCache && state.adminGlassesCache.length > 0
    ? state.adminGlassesCache
    : state.activeGlassesCache;
}

function renderAdminOverview() {
  const container = document.getElementById('admin-overview-grid');
  if (!container) return;

  const overview = state.adminOverview || {};
  const tiles = [
    { label: 'Usuarios', value: overview.users ?? 0, hint: `${overview.admins ?? 0} administradores`, accent: 'emerald' },
    { label: 'Recetas', value: overview.recipes ?? 0, hint: `${overview.enabled_recipes ?? 0} activas`, accent: 'blue' },
    { label: 'Vasos', value: overview.glasses ?? 0, hint: `${overview.enabled_glasses ?? 0} habilitados`, accent: 'orange' },
    { label: 'Líquidos', value: overview.liquids ?? 0, hint: 'Disponibles en depósitos', accent: 'rose' },
    { label: 'Depósitos', value: overview.tanks ?? 0, hint: 'Inventario físico', accent: 'slate' },
    { label: 'Eventos', value: overview.events ?? 0, hint: 'Actividad registrada', accent: 'emerald' },
  ];

  container.innerHTML = tiles.map(tile => `
    <article class="overview-tile overview-${tile.accent}">
      <span class="overview-label">${escapeHtml(tile.label)}</span>
      <strong class="overview-value">${escapeHtml(tile.value)}</strong>
      <span class="overview-hint">${escapeHtml(tile.hint)}</span>
    </article>
  `).join('');
}

function renderFavoriteMixOptions(selected = '') {
  const select = document.getElementById('au-favorite');
  if (!select) return;

  const recipes = state.adminRecipesCache || [];
  const existing = new Set(recipes.map(recipe => String(recipe.name || '').trim().toLowerCase()));
  const options = [
    '<option value="">-- Sin favorita --</option>',
    ...recipes.map(recipe => `<option value="${escapeHtml(recipe.name || '')}">${escapeHtml(recipe.name || '')}</option>`),
  ];

  if (selected && !existing.has(String(selected).trim().toLowerCase())) {
    options.splice(1, 0, `<option value="${escapeHtml(selected)}">${escapeHtml(selected)}</option>`);
  }

  select.innerHTML = options.join('');
  select.value = selected || '';
}

function renderAdminUsers() {
  const list = document.getElementById('admin-users-list');
  const count = document.getElementById('admin-users-count');
  if (!list) return;

  const query = String(document.getElementById('admin-user-search')?.value || '').trim().toLowerCase();
  const users = (state.adminUsersCache || []).filter(user => {
    if (!query) return true;
    const haystack = [
      user.username,
      user.full_name,
      user.role,
      user.favorite_mix,
      user.theme_mode,
      user.accent_color,
      user.info,
      String(user.xp ?? ''),
      String(user.level ?? ''),
    ].join(' ').toLowerCase();
    return haystack.includes(query);
  });

  if (count) {
    count.innerText = `${users.length} usuario${users.length === 1 ? '' : 's'}`;
  }

  if (!users.length) {
    list.innerHTML = '<p class="blank-state">No hay usuarios que coincidan con la búsqueda.</p>';
    document.getElementById('admin-user-activity')?.classList.add('empty');
    document.getElementById('admin-user-activity') && (document.getElementById('admin-user-activity').innerHTML = '<p class="blank-state">Selecciona un usuario para ver su actividad reciente.</p>');
    return;
  }

  list.innerHTML = users.map(user => {
    const isSelected = Number(state.adminSelectedUserId || 0) === Number(user.id);
    const initials = String((user.full_name || user.username || '?').trim().charAt(0) || '?').toUpperCase();
    const avatar = user.avatar_url
      ? `<img src="${escapeHtml(user.avatar_url)}" class="admin-user-avatar" alt="${escapeHtml(user.full_name || user.username)}">`
      : `<div class="admin-user-avatar-fallback">${escapeHtml(initials)}</div>`;

    const roleLabel = user.role === 'admin' ? 'Administrador' : 'Usuario';
    const roleClass = user.role === 'admin' ? 'is-admin' : 'is-user';
    const themeLabel = user.theme_mode === 'light' ? 'Claro' : 'Oscuro';
    const accentLabel = user.accent_color || 'emerald';
    const archiveLabel = user.is_archived ? 'Restaurar' : 'Archivar';

    return `
      <article class="admin-user-card ${isSelected ? 'selected' : ''}" data-action="view-user-activity" data-user-id="${user.id}">
        <div class="admin-user-head">
          <div class="admin-user-identity">
            ${avatar}
            <div class="admin-user-titlebox">
              <strong class="admin-user-name">${escapeHtml(user.full_name || user.username || 'Usuario')}</strong>
              <span class="admin-user-handle">@${escapeHtml(user.username || 'sin-usuario')}</span>
            </div>
          </div>
          <div class="admin-user-chipset">
            <span class="admin-chip ${roleClass}">${escapeHtml(roleLabel)}</span>
            <span class="admin-chip">LVL ${escapeHtml(user.level ?? 1)}</span>
            ${user.is_archived ? '<span class="admin-chip archived">Archivado</span>' : ''}
          </div>
        </div>
        <div class="admin-user-metrics">
          <div class="admin-user-metric"><span>XP</span><strong>${escapeHtml(user.xp ?? 0)}</strong></div>
          <div class="admin-user-metric"><span>Consumos</span><strong>${escapeHtml(user.consumptions ?? 0)}</strong></div>
          <div class="admin-user-metric"><span>Tema</span><strong>${escapeHtml(themeLabel)}</strong></div>
          <div class="admin-user-metric"><span>Acento</span><strong>${escapeHtml(accentLabel)}</strong></div>
        </div>
        <div class="admin-user-notes">
          <div><span>Favorita</span><strong>${escapeHtml(user.favorite_mix || 'Sin favorita')}</strong></div>
          <div><span>Actividad</span><strong>${escapeHtml(user.last_activity ? formatRelativeTime(user.last_activity) : 'Sin registros')}</strong></div>
        </div>
        <p class="admin-user-info">${escapeHtml(user.info || 'Sin nota interna')}</p>
        <div class="admin-user-footer">
          <span class="admin-user-created">Alta: ${escapeHtml(user.created_at ? new Date(user.created_at).toLocaleDateString('es-ES') : 'sin fecha')}</span>
          <div class="admin-user-actions">
            <button class="btn btn-small btn-secondary" type="button" data-action="edit-user" data-user-id="${user.id}">Editar</button>
            <button class="btn btn-small btn-secondary" type="button" data-action="view-user-activity" data-user-id="${user.id}">Actividad</button>
            <button class="btn btn-small btn-secondary" type="button" data-action="archive-user" data-user-id="${user.id}" data-archived="${user.is_archived ? 'true' : 'false'}">${archiveLabel}</button>
            <button class="btn btn-small btn-danger" type="button" data-action="purge-user" data-user-id="${user.id}">Eliminar seguro</button>
          </div>
        </div>
      </article>
    `;
  }).join('');

  if (!state.adminSelectedUserId && users.length > 0) {
    state.adminSelectedUserId = users[0].id;
  }
  if (state.adminSelectedUserId) {
    renderAdminUserSelection();
  }
}

function renderAdminUserSelection() {
  document.querySelectorAll('.admin-user-card').forEach(card => {
    card.classList.toggle('selected', Number(card.dataset.userId || '0') === Number(state.adminSelectedUserId || 0));
  });
}

async function loadAdminOverview() {
  try {
    state.adminOverview = await apiGet('/api/admin/overview') || state.adminOverview;
  } catch (e) {
    state.adminOverview = state.adminOverview || {};
  }
  renderAdminOverview();
}

async function loadSettings() {
  await Promise.all([loadAdminGlasses(), loadAdminRecipes()]);

  try {
    const settings = await apiGet('/api/admin/settings');
    state.systemSettings = settings || state.systemSettings;
  } catch (e) {}

  await Promise.all([loadAdminUsers(), loadAdminOverview()]);

  const statusInput = document.getElementById('set-status');
  const tanksInput = document.getElementById('set-tanks');
  if (statusInput) statusInput.value = state.systemSettings.poll_status;
  if (tanksInput) tanksInput.value = state.systemSettings.poll_tanks;

  renderAdminLiquids();
  renderIngredientSelector();
  window.renderGlassSelector?.();
  window.renderServingModesEditor?.();
  renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  switchAdminSection(state.adminActiveSection || 'users');
  if (state.adminSelectedUserId) {
    loadAdminUserActivity(state.adminSelectedUserId);
  }
}

async function loadAdminGlasses() {
  try {
    const glasses = await apiGet('/api/admin/glasses');
    state.adminGlassesCache = glasses || [];
    renderAdminGlasses();
  } catch (e) {
    const list = document.getElementById('admin-glasses-list');
    if (list) list.innerHTML = '<p class="blank-state">No se pudieron cargar los vasos.</p>';
  }
}

async function loadAdminUsers() {
  try {
    const users = await apiGet('/api/admin/users');
    state.adminUsersCache = users || [];
    renderAdminUsers();
    if (state.adminSelectedUserId && !state.adminUsersCache.some(user => Number(user.id) === Number(state.adminSelectedUserId))) {
      state.adminSelectedUserId = state.adminUsersCache[0]?.id || null;
    }
  } catch (e) {
    const list = document.getElementById('admin-users-list');
    if (list) list.innerHTML = '<p class="blank-state">No se pudieron cargar los usuarios.</p>';
  }
}

function renderAdminUserActivity(payload = null) {
  const container = document.getElementById('admin-user-activity');
  if (!container) return;

  const data = payload || state.adminUserActivity || { user: null, items: [] };
  const user = data.user;
  const items = data.items || [];

  if (!user) {
    container.classList.add('empty');
    container.innerHTML = '<p class="blank-state">Selecciona un usuario para ver su actividad reciente.</p>';
    return;
  }

  container.classList.remove('empty');
  container.innerHTML = `
    <div class="admin-activity-summary">
      <div>
        <span class="admin-activity-label">Usuario seleccionado</span>
        <strong>${escapeHtml(user.full_name || user.username)}</strong>
        <p>${escapeHtml(user.username || '')}</p>
        <small>${escapeHtml(user.favorite_mix || 'Sin favorita')} · ${escapeHtml(user.theme_mode || 'dark')} · ${escapeHtml(user.accent_color || 'emerald')}</small>
      </div>
      <div>
        <span class="admin-activity-label">Estado</span>
        <strong>${user.is_archived ? 'Archivado' : 'Activo'}</strong>
        <p>${escapeHtml(user.role || 'user')} · LVL ${escapeHtml(user.level ?? 1)} · XP ${escapeHtml(user.xp ?? 0)}</p>
        <small>${escapeHtml(user.is_archived ? `Archivado por ${user.archived_by || 'sistema'}` : `Creado ${user.created_at ? new Date(user.created_at).toLocaleDateString('es-ES') : 'sin fecha'}`)}</small>
      </div>
    </div>
    <div class="admin-activity-timeline">
      ${items.length > 0 ? items.map(item => `
        <article class="admin-activity-item">
          <div class="admin-activity-item-main">
            <strong>${escapeHtml(item.recipe || 'Consumición')}</strong>
            <span>${escapeHtml(item.glass_type || '-')} · ${escapeHtml(item.serving_mode || '-')} · ${escapeHtml(item.status || 'done')}</span>
          </div>
          <div class="admin-activity-item-side">
            <strong>+${escapeHtml(item.xp ?? 0)} XP</strong>
            <span>${escapeHtml(item.time ? formatRelativeTime(item.time) : 'sin fecha')}</span>
          </div>
        </article>
      `).join('') : '<p class="blank-state">Este usuario todavía no tiene actividad registrada.</p>'}
    </div>
  `;
}

async function loadAdminUserActivity(userId) {
  if (!userId) return;
  try {
    const payload = await apiGet(`/api/admin/users/${userId}/activity`);
    state.adminUserActivity = payload || { user: null, items: [] };
    renderAdminUserActivity(state.adminUserActivity);
  } catch (e) {
    state.adminUserActivity = { user: null, items: [] };
    renderAdminUserActivity();
  }
}

function selectAdminUser(userId) {
  state.adminSelectedUserId = Number(userId);
  renderAdminUserSelection();
  loadAdminUserActivity(userId);
}

function switchAdminSection(section) {
  const normalized = section || 'users';
  state.adminActiveSection = normalized;
  document.querySelectorAll('[data-admin-section]').forEach(el => {
    el.classList.toggle('active', el.dataset.adminSection === normalized);
  });
  document.querySelectorAll('[data-action="switch-admin-section"]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.section === normalized);
  });
}

async function archiveUser(userId, isArchived = false) {
  const target = (state.adminUsersCache || []).find(user => Number(user.id) === Number(userId));
  if (!target) return;
  const nextArchived = !isArchived;
  const confirmMessage = nextArchived
    ? `¿Archivar a ${target.username}? No podrá iniciar sesión hasta restaurarlo.`
    : `¿Restaurar a ${target.username}?`;
  if (!confirm(confirmMessage)) return;

  try {
    await apiPost(`/api/admin/users/${userId}/archive`, { is_archived: nextArchived });
    await loadAdminUsers();
    await loadAdminOverview();
    if (Number(state.adminSelectedUserId || 0) === Number(userId)) {
      await loadAdminUserActivity(userId);
    }
  } catch (e) {
    alert(`No se pudo cambiar el estado del usuario: ${e?.message || 'desconocido'}`);
  }
}

async function purgeUser(userId) {
  const target = (state.adminUsersCache || []).find(user => Number(user.id) === Number(userId));
  if (!target) return;
  if (!target.is_archived) {
    alert('Archiva primero al usuario antes de eliminarlo de forma segura.');
    return;
  }
  if (!confirm(`Eliminar de forma segura a ${target.username}? Esta acción solo se permite sobre usuarios archivados sin historial.`)) return;

  try {
    const response = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE', headers: authHeaders() });
    if (!response.ok) {
      let payload = null;
      try {
        payload = await response.json();
      } catch (error) {
        payload = await response.text().catch(() => '');
      }
      const detail = payload && typeof payload === 'object' ? (payload.detail || payload.message || payload.error) : payload;
      throw new Error(typeof detail === 'string' && detail.trim() ? detail : `Error ${response.status}`);
    }
    state.adminSelectedUserId = null;
    state.adminUserActivity = { user: null, items: [] };
    await loadAdminUsers();
    await loadAdminOverview();
    renderAdminUserActivity();
  } catch (e) {
    alert(`No se pudo eliminar el usuario: ${e?.message || 'desconocido'}`);
  }
}

function createUser(ev) {
  ev?.preventDefault?.();
  openUserForm();
}

function openUserForm() {
  resetUserForm();
  renderFavoriteMixOptions();
  document.getElementById('user-modal')?.classList.add('open');
  document.getElementById('au-username')?.focus();
}

function resetUserForm() {
  const form = document.getElementById('user-form');
  if (form) form.reset();

  document.getElementById('au-id').value = '';
  document.getElementById('au-username').value = '';
  document.getElementById('au-fullname').value = '';
  document.getElementById('au-password').value = '';
  document.getElementById('au-password').placeholder = 'Contraseña';
  document.getElementById('au-password').required = true;
  document.getElementById('au-role').value = 'user';
  document.getElementById('au-xp').value = 0;
  document.getElementById('au-level').value = 1;
  document.getElementById('au-favorite').value = '';
  document.getElementById('au-theme').value = 'dark';
  document.getElementById('au-accent').value = 'emerald';
  document.getElementById('au-info').value = '';
  document.getElementById('au-avatar-url').value = '';
  document.getElementById('au-submit').innerText = 'Crear usuario';
  document.getElementById('user-modal-title').innerText = 'Nuevo usuario';
  document.getElementById('user-modal')?.classList.remove('open');
}

function closeUserForm() {
  resetUserForm();
}

function editUser(userId) {
  const user = (state.adminUsersCache || []).find(item => Number(item.id) === Number(userId));
  if (!user) return;

  resetUserForm();
  renderFavoriteMixOptions(user.favorite_mix || '');
  document.getElementById('au-id').value = user.id;
  document.getElementById('au-username').value = user.username || '';
  document.getElementById('au-fullname').value = user.full_name || '';
  document.getElementById('au-password').value = '';
  document.getElementById('au-password').placeholder = 'Nueva contraseña opcional';
  document.getElementById('au-password').required = false;
  document.getElementById('au-role').value = user.role || 'user';
  document.getElementById('au-xp').value = user.xp ?? 0;
  document.getElementById('au-level').value = user.level ?? 1;
  document.getElementById('au-favorite').value = user.favorite_mix || '';
  document.getElementById('au-theme').value = user.theme_mode || 'dark';
  document.getElementById('au-accent').value = user.accent_color || 'emerald';
  document.getElementById('au-info').value = user.info || '';
  document.getElementById('au-avatar-url').value = user.avatar_url || '';
  document.getElementById('au-submit').innerText = 'Guardar usuario';
  document.getElementById('user-modal-title').innerText = `Editar usuario · ${user.username}`;
  document.getElementById('user-modal')?.classList.add('open');
  document.getElementById('au-username')?.focus();
}

async function saveUser(ev) {
  ev.preventDefault();
  const userId = Number(document.getElementById('au-id').value || '0');
  const payload = {
    username: document.getElementById('au-username').value.trim(),
    full_name: document.getElementById('au-fullname').value.trim(),
    role: document.getElementById('au-role').value,
    xp: Number(document.getElementById('au-xp').value || 0),
    level: Number(document.getElementById('au-level').value || 1),
    favorite_mix: document.getElementById('au-favorite').value || null,
    info: document.getElementById('au-info').value,
    theme_mode: document.getElementById('au-theme').value,
    accent_color: document.getElementById('au-accent').value,
    avatar_url: document.getElementById('au-avatar-url').value.trim(),
  };

  const password = document.getElementById('au-password').value.trim();
  if (password) payload.password = password;

  try {
    if (userId > 0) {
      await apiPost(`/api/admin/users/${userId}`, payload);
    } else {
      if (!payload.password) {
        alert('La contraseña es obligatoria para crear un usuario.');
        return;
      }
      await apiPost('/api/admin/users/create', {
        username: payload.username,
        password: payload.password,
        full_name: payload.full_name,
        role: payload.role,
        xp: payload.xp,
        level: payload.level,
        favorite_mix: payload.favorite_mix,
        info: payload.info,
        theme_mode: payload.theme_mode,
        accent_color: payload.accent_color,
        avatar_url: payload.avatar_url,
      });
    }

    closeUserForm();
    await loadAdminUsers();
    await loadAdminOverview();
  } catch (e) {
    alert(`Error al guardar usuario: ${e?.message || 'desconocido'}`);
  }
}

function renderAdminLiquids() {
  const list = document.getElementById('admin-liquids-list');
  if (!list) return;
  const liquids = state.systemSettings.liquids || [];
  if (!liquids.length) {
    list.innerHTML = '<p class="blank-state">No hay líquidos configurados.</p>';
    return;
  }

  list.innerHTML = liquids.map((l, i) => `
    <div class="liquid-row">
      <span><strong class="liquid-name">${escapeHtml(l.name)}</strong> <span class="muted liquid-type">(${escapeHtml(String(l.type || '').toUpperCase())})</span></span>
      <div class="liquid-row-actions">
        <button class="btn btn-small btn-secondary" type="button" data-action="edit-liquid" data-index="${i}">Editar</button>
        <button class="btn btn-small btn-danger" type="button" data-action="delete-liquid" data-index="${i}">X</button>
      </div>
    </div>
  `).join('');
}

function renderAdminGlasses() {
  const list = document.getElementById('admin-glasses-list');
  if (!list) return;

  if (!state.adminGlassesCache || state.adminGlassesCache.length === 0) {
    list.innerHTML = '<p class="muted liquid-empty">No hay vasos configurados.</p>';
    return;
  }

  list.innerHTML = state.adminGlassesCache.map(glass => {
    const stateText = glass.enabled ? 'Habilitado' : 'Deshabilitado';
    return `
      <div class="glass-card liquid-card">
        <div class="glass-icon-row">
          <div class="glass-emoji">${escapeHtml(glass.icon || '🥤')}</div>
          <div class="glass-meta-wrap">
            <strong class="liquid-name">${escapeHtml(glass.name || glass.key)}</strong>
            <div class="glass-meta">Clave: ${escapeHtml(glass.key)} · ${Number(glass.capacity_ml || 0)} mL · ${stateText}</div>
          </div>
        </div>
        <div class="liquid-card-actions">
          <button class="btn btn-small btn-secondary" type="button" data-action="edit-glass" data-glass-id="${glass.id}">Editar</button>
          <button class="btn btn-small btn-danger" type="button" data-action="delete-glass" data-glass-id="${glass.id}">X</button>
        </div>
      </div>
    `;
  }).join('');
}

function syncGlassKey() {
  const keyInput = document.getElementById('gl-key');
  const nameInput = document.getElementById('gl-name');
  if (!keyInput || !nameInput) return;
  keyInput.value = slugifyGlassKey(nameInput.value);
}

function resetGlassForm() {
  const form = document.getElementById('glass-form');
  if (form) form.reset();
  document.getElementById('gl-id').value = '';
  document.getElementById('gl-key').value = '';
  document.getElementById('gl-name').value = '';
  document.getElementById('gl-icon').value = '🥤';
  document.getElementById('gl-capacity').value = 300;
  document.getElementById('gl-enabled').checked = true;
  document.getElementById('gl-submit').innerText = 'Añadir vaso';
  document.getElementById('glass-modal')?.classList.remove('open');
}

function openGlassForm() {
  resetGlassForm();
  document.getElementById('glass-modal')?.classList.add('open');
  document.getElementById('gl-name')?.focus();
}

function closeGlassForm() {
  resetGlassForm();
}

function editGlass(id) {
  const glass = (state.adminGlassesCache || []).find(g => Number(g.id) === Number(id));
  if (!glass) return;

  resetGlassForm();
  document.getElementById('glass-modal')?.classList.add('open');
  document.getElementById('gl-id').value = glass.id;
  document.getElementById('gl-key').value = glass.key || '';
  document.getElementById('gl-name').value = glass.name || '';
  document.getElementById('gl-icon').value = glass.icon || '🥤';
  document.getElementById('gl-capacity').value = glass.capacity_ml || 300;
  document.getElementById('gl-enabled').checked = glass.enabled !== false;
  document.getElementById('gl-submit').innerText = 'Guardar vaso';
  document.getElementById('glass-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function saveGlass(ev) {
  ev.preventDefault();
  const glassId = parseInt(document.getElementById('gl-id').value || '0');
  const payload = {
    name: document.getElementById('gl-name').value,
    icon: document.getElementById('gl-icon').value || '🥤',
    capacity_ml: parseInt(document.getElementById('gl-capacity').value || '300'),
    enabled: document.getElementById('gl-enabled').checked,
  };

  try {
    if (glassId > 0) {
      await apiPost(`/api/admin/glasses/${glassId}`, payload);
    } else {
      await apiPost('/api/admin/glasses/create', { ...payload, key: document.getElementById('gl-key').value || slugifyGlassKey(payload.name) });
    }
    closeGlassForm();
    await loadAdminGlasses();
    await window.loadActiveGlasses?.();
    await window.loadRecipes?.();
    renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  } catch (e) {
    alert('Error al guardar el vaso.');
  }
}

async function deleteGlass(id) {
  if (!confirm('¿Eliminar este vaso? Se retirará de las recetas donde aparezca.')) return;
  try {
    await fetch(`/api/admin/glasses/${id}`, { method: 'DELETE', headers: authHeaders() });
    if (Number(document.getElementById('gl-id').value || '0') === Number(id)) {
      closeGlassForm();
    }
    await loadAdminGlasses();
    await window.loadActiveGlasses?.();
    await window.loadRecipes?.();
    renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  } catch (e) {
    alert('Error al eliminar el vaso.');
  }
}

function resetLiquidForm() {
  const form = document.getElementById('liquid-form');
  if (form) form.reset();
  document.getElementById('liq-id').value = '';
  document.getElementById('new-liq-name').value = '';
  document.getElementById('new-liq-type').value = 'mixer';
  document.getElementById('liq-submit').innerText = 'Añadir líquido';
  document.getElementById('liquid-modal')?.classList.remove('open');
}

function openLiquidForm() {
  resetLiquidForm();
  document.getElementById('liquid-modal')?.classList.add('open');
  document.getElementById('new-liq-name')?.focus();
}

function closeLiquidForm() {
  resetLiquidForm();
}

function editLiquid(index) {
  const liquid = (state.systemSettings.liquids || [])[Number(index)];
  if (!liquid) return;

  resetLiquidForm();
  document.getElementById('liquid-modal')?.classList.add('open');
  document.getElementById('liq-id').value = String(index);
  document.getElementById('new-liq-name').value = liquid.name || '';
  document.getElementById('new-liq-type').value = liquid.type || 'mixer';
  document.getElementById('liq-submit').innerText = 'Guardar líquido';
}

async function saveLiquid(ev) {
  ev.preventDefault();
  const name = document.getElementById('new-liq-name').value.trim();
  const type = document.getElementById('new-liq-type').value;
  const liquidIndex = Number(document.getElementById('liq-id').value || '-1');
  if (!name) return;

  try {
    let response = null;
    if (Number.isInteger(liquidIndex) && liquidIndex >= 0) {
      response = await apiPost(`/api/admin/settings/liquids/${liquidIndex}`, { name, type });
      if (response?.renamed_from && response.renamed_from !== name) {
        state.selectedIngredients = state.selectedIngredients.map(item => item === response.renamed_from ? name : item);
      }
    } else {
      const liquids = [...(state.systemSettings.liquids || []), { name, type }];
      response = await apiPost('/api/admin/settings', { ...state.systemSettings, liquids });
    }

    state.systemSettings = response?.settings || response || state.systemSettings;
    closeLiquidForm();
    renderAdminLiquids();
    renderIngredientSelector();
    window.renderServingModesEditor?.();
    window.renderTanks?.();
    await loadAdminRecipes();
    await window.loadRecipes?.();
    renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  } catch (e) {
    alert(`Error al guardar el líquido: ${e?.message || 'desconocido'}`);
  }
}

async function deleteLiquid(index) {
  const liquids = [...(state.systemSettings.liquids || [])];
  liquids.splice(index, 1);
  const response = await apiPost('/api/admin/settings', { ...state.systemSettings, liquids });
  state.systemSettings = response?.settings || response || state.systemSettings;
  state.selectedIngredients = state.selectedIngredients.filter(name => (state.systemSettings.liquids || []).some(l => l.name === name));
  renderAdminLiquids();
  renderIngredientSelector();
  window.renderServingModesEditor?.();
  window.renderTanks?.();
  renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  window.loadRecipes?.();
}

async function saveSettings(ev) {
  ev.preventDefault();
  state.systemSettings.poll_status = parseInt(document.getElementById('set-status').value);
  state.systemSettings.poll_tanks = parseInt(document.getElementById('set-tanks').value);
  await apiPost('/api/admin/settings', state.systemSettings);
  alert('Configuración guardada');
}

function renderIngredientSelector() {
  const container = document.getElementById('nr-ing-selector');
  if (!container) return;

  const liquids = state.systemSettings.liquids || [];
  container.innerHTML = liquids.map(l => {
    const isSelected = state.selectedIngredients.includes(l.name);
    return `
      <div class="ingredient-tag liquid-ingredient ${isSelected ? 'selected' : ''}" data-action="toggle-ingredient" data-ingredient-name="${l.name}">
        <span class="tag-main">${escapeHtml(l.name)}</span>
        <span class="tag-check">${isSelected ? '✓' : '+'}</span>
      </div>
    `;
  }).join('');

  const hidden = document.getElementById('nr-ing-hidden');
  if (hidden) hidden.value = state.selectedIngredients.join(', ');
}

function toggleIngredient(name) {
  if (state.selectedIngredients.includes(name)) {
    state.selectedIngredients = state.selectedIngredients.filter(n => n !== name);
  } else {
    state.selectedIngredients.push(name);
  }
  renderIngredientSelector();
  window.renderServingModesEditor?.();
}

function resetRecipeForm() {
  const form = document.getElementById('add-recipe-form');
  if (form) form.reset();

  document.getElementById('nr-id').value = '';
  document.getElementById('nr-name').value = '';
  document.getElementById('nr-desc').value = '';
  document.getElementById('nr-xp').value = 150;

  state.selectedIngredients = [];
  const defaultGlassSource = getAdminGlassSource();
  state.selectedGlasses = defaultGlassSource.length > 0
    ? [defaultGlassSource[0].key]
    : ['highball'];

  document.getElementById('nr-submit').innerText = 'Añadir Receta';
  renderIngredientSelector();
  window.renderGlassSelector?.();
  window.renderServingModesEditor?.();
  document.getElementById('recipe-modal')?.classList.remove('open');
}

function openRecipeForm() {
  resetRecipeForm();
  document.getElementById('recipe-modal')?.classList.add('open');
  document.getElementById('nr-name')?.focus();
}

function closeRecipeForm(ev = null) {
  resetRecipeForm();
}

async function addRecipe(ev) {
  ev.preventDefault();
  const reqs = document.getElementById('nr-ing-hidden').value;
  if (!reqs) {
    alert('Selecciona al menos un líquido requerido.');
    return;
  }

  const recipeId = parseInt(document.getElementById('nr-id').value || '0');
  const servingModes = normalizeModeMap(window.collectServingModes?.() || {}, state.selectedIngredients);

  const payload = {
    name: document.getElementById('nr-name').value,
    description: document.getElementById('nr-desc').value,
    ingredients: reqs,
    xp_reward: parseInt(document.getElementById('nr-xp').value),
    glass_options: state.selectedGlasses.slice(),
    serving_modes: servingModes,
  };

  try {
    if (recipeId > 0) {
      await apiPost(`/api/admin/recipes/${recipeId}`, payload);
    } else {
      await apiPost('/api/admin/recipes/create', payload);
    }
    closeRecipeForm();
    await loadAdminRecipes();
    await window.loadRecipes?.();
    renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  } catch (e) {
    alert(`Error al crear receta: ${e?.message || 'desconocido'}`);
  }
}

async function loadAdminRecipes() {
  try {
    const recipes = await apiGet('/api/admin/recipes');
    state.adminRecipesCache = recipes || [];
    const list = document.getElementById('admin-recipes-list');
    if (list) {
      list.innerHTML = (recipes || []).map(r => {
        const glasses = (r.glass_options || []).join(', ') || '-';
        const modes = Object.keys(r.serving_modes || {}).join(', ') || '-';
        return `
          <div class="recipe-row-panel">
            <div class="recipe-row-body">
              <div>
                <strong class="recipe-heading">${escapeHtml(r.name)}</strong><br>
                <span class="recipe-stats">Reqs: ${escapeHtml(r.ingredients)}</span><br>
                <span class="recipe-stats-sm">Vasos: ${escapeHtml(glasses)}</span><br>
                <span class="recipe-stats-sm">Modos: ${escapeHtml(modes)}</span>
              </div>
            </div>
            <div class="recipe-row-actions">
              <button class="btn btn-small btn-secondary" type="button" data-action="edit-recipe" data-recipe-id="${r.id}">Editar</button>
              <button class="btn btn-small btn-danger" type="button" data-action="delete-recipe" data-recipe-id="${r.id}">X</button>
            </div>
          </div>
        `;
      }).join('');
    }
    renderFavoriteMixOptions(document.getElementById('au-favorite')?.value || '');
  } catch (e) {}
}

function editRecipe(id) {
  const recipe = (state.adminRecipesCache || []).find(r => Number(r.id) === Number(id));
  if (!recipe) return;

  openRecipeForm();

  document.getElementById('nr-id').value = recipe.id;
  document.getElementById('nr-name').value = recipe.name || '';
  document.getElementById('nr-desc').value = recipe.description || '';
  document.getElementById('nr-xp').value = recipe.xp_reward || 150;

  const recipeIngredients = new Set(
    String(recipe.ingredients || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .map(s => s.toLowerCase())
  );

  state.selectedIngredients = (recipe.ingredients || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .filter(name => recipeIngredients.has(name.toLowerCase()) || recipeIngredients.size === 0);

  const knownLiquids = (state.systemSettings.liquids || []).map(l => l.name);
  if (knownLiquids.length > 0) {
    const matched = knownLiquids.filter(name => recipeIngredients.has(name.toLowerCase()));
    const unmatched = state.selectedIngredients.filter(name => !knownLiquids.some(liq => liq.toLowerCase() === name.toLowerCase()));
    state.selectedIngredients = [...matched, ...unmatched];
  }

  const normalizedGlasses = Array.isArray(recipe.glass_options)
    ? recipe.glass_options.map(key => String(key).trim().toLowerCase()).filter(Boolean)
    : [];
  const knownGlasses = getAdminGlassSource().map(glass => glass.key);
  state.selectedGlasses = normalizedGlasses.filter(key => knownGlasses.includes(key));
  if (state.selectedGlasses.length === 0) {
    state.selectedGlasses = knownGlasses.slice(0, 1);
  }

  renderIngredientSelector();
  window.renderGlassSelector?.();
  window.renderServingModesEditor?.(recipe.serving_modes || {});

  document.getElementById('nr-submit').innerText = 'Guardar cambios';
  document.getElementById('add-recipe-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function deleteRecipe(id) {
  await fetch(`/api/admin/recipes/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (parseInt(document.getElementById('nr-id').value || '0') === Number(id)) {
    resetRecipeForm();
  }
  await loadAdminRecipes();
  await window.loadRecipes?.();
}

async function reloadAdminPanel() {
  await loadSettings();
}

Object.assign(window, {
  loadSettings,
  loadAdminOverview,
  loadAdminGlasses,
  loadAdminUsers,
  createUser,
  openUserForm,
  closeUserForm,
  resetUserForm,
  editUser,
  selectAdminUser,
  switchAdminSection,
  archiveUser,
  purgeUser,
  saveUser,
  renderAdminOverview,
  renderAdminUsers,
  renderAdminUserSelection,
  renderAdminUserActivity,
  loadAdminUserActivity,
  renderFavoriteMixOptions,
  renderAdminLiquids,
  renderAdminGlasses,
  syncGlassKey,
  resetGlassForm,
  openGlassForm,
  closeGlassForm,
  editGlass,
  saveGlass,
  deleteGlass,
  openLiquidForm,
  closeLiquidForm,
  resetLiquidForm,
  editLiquid,
  saveLiquid,
  deleteLiquid,
  saveSettings,
  renderIngredientSelector,
  toggleIngredient,
  resetRecipeForm,
  openRecipeForm,
  closeRecipeForm,
  addRecipe,
  loadAdminRecipes,
  editRecipe,
  deleteRecipe,
  reloadAdminPanel,
});
