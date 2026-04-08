const dashboard = window.cubatronDashboard;
const state = dashboard.state;
const { escapeHtml, getGlassInfo, getRecipeGlassOptions, computeServeXp, buildLiquidBreakdown, normalizeModeMap, slugifyGlassKey } = dashboard.utils;
const { apiGet, apiPost, authHeaders } = dashboard.api;
const CUSTOM_PROFILE_STEP = 0.5;

function clampCustomPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.max(0, Math.min(100, Math.round(numeric / CUSTOM_PROFILE_STEP) * CUSTOM_PROFILE_STEP));
}

function formatCustomPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '0';
  const rounded = Math.round(numeric * 10) / 10;
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1).replace(/\.0$/, '');
}

function redistributeCustomProfile(currentProfile, liquids, activeLiquid, activeValue) {
  const orderedLiquids = Array.isArray(liquids) ? liquids.filter(Boolean) : [];
  const nextProfile = {};
  if (orderedLiquids.length === 0) return nextProfile;

  const activePercent = clampCustomPercent(activeValue);
  const activeUnits = Math.round(activePercent / CUSTOM_PROFILE_STEP);
  const totalUnits = Math.round(100 / CUSTOM_PROFILE_STEP);
  nextProfile[activeLiquid] = activePercent;

  const anchorLiquid = orderedLiquids.length > 2 && state.activeServeCustomLastLiquid && state.activeServeCustomLastLiquid !== activeLiquid
    ? state.activeServeCustomLastLiquid
    : null;

  const anchorPercent = anchorLiquid ? clampCustomPercent(currentProfile?.[anchorLiquid] || 0) : 0;
  const anchorUnits = Math.round(anchorPercent / CUSTOM_PROFILE_STEP);
  const remainingUnits = Math.max(0, totalUnits - activeUnits - anchorUnits);
  const otherLiquids = orderedLiquids.filter(liquid => liquid !== activeLiquid && liquid !== anchorLiquid);

  if (anchorLiquid) {
    nextProfile[anchorLiquid] = anchorPercent;
  }

  if (!anchorLiquid && otherLiquids.length === 0) {
    nextProfile[activeLiquid] = 100;
    return nextProfile;
  }

  if (anchorLiquid && activeUnits + anchorUnits > totalUnits) {
    nextProfile[anchorLiquid] = Math.max(0, (totalUnits - activeUnits) * CUSTOM_PROFILE_STEP);
    return nextProfile;
  }

  if (otherLiquids.length === 0) {
    return nextProfile;
  }

  if (otherLiquids.length === 1) {
    nextProfile[otherLiquids[0]] = remainingUnits * CUSTOM_PROFILE_STEP;
    return nextProfile;
  }

  const weights = otherLiquids.map(liquid => {
    const numeric = Number(currentProfile?.[liquid]);
    return Number.isFinite(numeric) && numeric > 0 ? numeric : 1;
  });
  const totalWeight = weights.reduce((sum, value) => sum + value, 0) || otherLiquids.length;

  const provisional = otherLiquids.map((liquid, index) => {
    const exactUnits = (weights[index] / totalWeight) * remainingUnits;
    const baseUnits = Math.floor(exactUnits);
    return {
      liquid,
      units: baseUnits,
      remainder: exactUnits - baseUnits,
    };
  });

  let allocatedUnits = provisional.reduce((sum, item) => sum + item.units, 0);
  let leftoverUnits = remainingUnits - allocatedUnits;
  provisional.sort((a, b) => b.remainder - a.remainder);
  for (let index = 0; index < provisional.length && leftoverUnits > 0; index += 1, leftoverUnits -= 1) {
    provisional[index].units += 1;
  }

  provisional.forEach(item => {
    nextProfile[item.liquid] = item.units * CUSTOM_PROFILE_STEP;
  });

  return nextProfile;
}

function getRecipeLiquidOrder(recipe) {
  const seen = new Set();
  const liquids = [];

  const pushLiquid = (value) => {
    const liquid = String(value || '').trim();
    if (!liquid || seen.has(liquid)) return;
    seen.add(liquid);
    liquids.push(liquid);
  };

  String(recipe?.ingredients || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean)
    .forEach(pushLiquid);

  Object.values(recipe?.serving_modes || {}).forEach(profile => {
    Object.keys(profile || {}).forEach(pushLiquid);
  });

  return liquids;
}

function normalizeCustomProfile(profile, liquids) {
  const orderedLiquids = Array.isArray(liquids) ? liquids.filter(Boolean) : [];
  if (orderedLiquids.length === 0) return {};

  const safe = {};
  orderedLiquids.forEach(liquid => {
    const value = Number(profile?.[liquid]);
    safe[liquid] = Number.isFinite(value) && value > 0 ? value : 0;
  });

  const total = orderedLiquids.reduce((sum, liquid) => sum + safe[liquid], 0);
  if (total <= 0) {
    const base = Math.floor(100 / orderedLiquids.length);
    let remainder = 100 - (base * orderedLiquids.length);
    orderedLiquids.forEach((liquid, index) => {
      safe[liquid] = base + (index < remainder ? 1 : 0);
    });
    return safe;
  }

  let allocated = 0;
  orderedLiquids.forEach((liquid, index) => {
    if (index === orderedLiquids.length - 1) {
      safe[liquid] = Math.max(0, 100 - allocated);
      return;
    }
    const value = Math.floor((safe[liquid] / total) * 100);
    safe[liquid] = value;
    allocated += value;
  });

  return safe;
}

function getServeModeProfile(recipe, mode) {
  if (mode === 'custom') {
    return state.activeServeCustomProfile || {};
  }
  return recipe?.serving_modes?.[mode] || {};
}

function ensureCustomServeProfile(recipe) {
  const liquids = getRecipeLiquidOrder(recipe);
  if (liquids.length === 0) {
    state.activeServeCustomProfile = {};
    state.activeServeCustomLastLiquid = null;
    return state.activeServeCustomProfile;
  }

  const currentKeys = Object.keys(state.activeServeCustomProfile || {});
  const matchesLiquids = currentKeys.length === liquids.length && liquids.every(liquid => currentKeys.includes(liquid));
  if (matchesLiquids) {
    return state.activeServeCustomProfile;
  }

  const fallbackMode = ['medium', 'high', 'low', 'extreme'].find(mode => recipe?.serving_modes?.[mode]);
  const fallbackProfile = fallbackMode ? recipe.serving_modes[fallbackMode] : {};
  state.activeServeCustomProfile = normalizeCustomProfile(fallbackProfile, liquids);
  state.activeServeCustomLastLiquid = null;
  return state.activeServeCustomProfile;
}

function updateCustomServeProfile(liquid, nextValue) {
  if (!state.activeServeRecipe) return;

  const liquids = getRecipeLiquidOrder(state.activeServeRecipe);
  if (!liquids.length || !liquids.includes(liquid)) return;

  const currentProfile = ensureCustomServeProfile(state.activeServeRecipe);
  state.activeServeCustomProfile = redistributeCustomProfile(currentProfile, liquids, liquid, nextValue);
  state.activeServeCustomLastLiquid = liquid;
  syncCustomServeEditor();
  updateServeEstimate();
}

function syncCustomServeEditor() {
  const container = document.getElementById('serve-custom-editor');
  if (!container || container.hidden || !state.activeServeRecipe) return;

  const liquids = getRecipeLiquidOrder(state.activeServeRecipe);
  const profile = state.activeServeCustomProfile || {};
  const total = liquids.reduce((sum, liquid) => sum + Math.max(0, Number(profile[liquid]) || 0), 0);

  const totalEl = container.querySelector('.serve-custom-total');
  if (totalEl) totalEl.innerText = `${total}%`;

  liquids.forEach(liquid => {
    const value = Math.max(0, Number(profile[liquid]) || 0);
    const row = container.querySelector(`.serve-custom-row [data-liquid="${CSS.escape(liquid)}"]`);
    if (row) {
      row.value = formatCustomPercent(value);
    }
    const label = container.querySelector(`.serve-custom-row [data-liquid="${CSS.escape(liquid)}"]`)
      ?.closest('.serve-custom-row')?.querySelector('.serve-custom-row-head span');
    if (label) label.innerText = `${formatCustomPercent(value)}%`;
  });
}

function renderGlassSelector() {
  const container = document.getElementById('nr-glass-selector');
  if (!container) return;
  const sourceGlasses = (state.adminGlassesCache && state.adminGlassesCache.length > 0)
    ? state.adminGlassesCache
    : state.activeGlassesCache;
  const keys = sourceGlasses.filter(g => g.enabled !== false).map(g => g.key);
  if (keys.length === 0) {
    container.innerHTML = '<p class="blank-state">No hay vasos habilitados.</p>';
    return;
  }
  container.innerHTML = keys.map(k => {
    const g = getGlassInfo(k);
    const selected = state.selectedGlasses.includes(k);
    return `<div class="glass-tag ${selected ? 'active' : ''}" data-action="toggle-glass" data-glass-key="${k}"><span class="tag-emoji">${escapeHtml(g.icon || '🥤')}</span><span class="tag-main">${escapeHtml(g.name || g.label || k)}</span><span class="tag-check">${selected ? '✓' : '+'}</span></div>`;
  }).join('');
}

function toggleGlass(glassKey) {
  if (state.selectedGlasses.includes(glassKey)) {
    if (state.selectedGlasses.length === 1) return;
    state.selectedGlasses = state.selectedGlasses.filter(g => g !== glassKey);
  } else {
    state.selectedGlasses.push(glassKey);
  }
  renderGlassSelector();
}

function renderServingModesEditor(existing = null) {
  const container = document.getElementById('nr-serving-modes');
  if (!container) return;

  const selected = state.selectedIngredients.slice();
  const sourceModes = existing || collectServingModes();
  const safeModes = normalizeModeMap(sourceModes, selected);

  container.innerHTML = dashboard.constants.SERVE_MODES.map(mode => {
    const rows = selected.map(liq => {
      const value = safeModes[mode][liq] ?? 0;
      return `<div class="serve-row"><span class="serve-text">${liq}</span><input class="form-control" type="number" min="0" max="100" step="1" data-mode="${mode}" data-liq="${liq}" value="${value}"><span>%</span></div>`;
    }).join('') || '<p class="blank-state">Selecciona ingredientes para definir porcentajes.</p>';

    return `<div class="serve-mode-box"><h4>${mode}</h4>${rows}</div>`;
  }).join('');
}

function collectServingModes() {
  const modes = {};
  dashboard.constants.SERVE_MODES.forEach(mode => modes[mode] = {});
  document.querySelectorAll('#nr-serving-modes input[data-mode][data-liq]').forEach(el => {
    const mode = el.dataset.mode;
    const liq = el.dataset.liq;
    const value = Number(el.value);
    modes[mode][liq] = Number.isFinite(value) ? value : 0;
  });
  return modes;
}

function getRecipeById(id) {
  return state.recipesCache.find(r => Number(r.id) === Number(id));
}

function computeServeMl(glassKey) {
  return Number(getGlassInfo(glassKey).capacity_ml || 300);
}

function updateServeEstimate() {
  const estimateEl = document.getElementById('serve-ml-estimate');
  const xpEl = document.getElementById('serve-xp-estimate');
  const breakdownEl = document.getElementById('serve-breakdown');
  if (!estimateEl || !xpEl || !breakdownEl || !state.activeServeRecipe) return;

  const glass = getGlassInfo(state.activeServeGlass);
  const totalMl = computeServeMl(state.activeServeGlass, state.activeServeMode);
  const profile = getServeModeProfile(state.activeServeRecipe, state.activeServeMode === 'custom' ? 'custom' : state.activeServeMode);
  const breakdown = buildLiquidBreakdown(profile, totalMl);
  const xpValue = computeServeXp(state.activeServeRecipe.xp_reward, totalMl, state.activeServeMode);

  estimateEl.innerText = `Vaso: ${glass.name || glass.label || state.activeServeGlass} · Capacidad fija: ${totalMl} ml`;
  xpEl.innerText = `XP estimado: ${xpValue}`;
  breakdownEl.innerHTML = breakdown.length > 0
    ? breakdown.map(item => {
      const pctText = `${item.pct}%`;
      return `<div class="serve-breakdown-row"><div class="serve-breakdown-bar"></div><div class="serve-breakdown-text"><strong>${escapeHtml(item.liquid)}: ${item.ml} ml</strong><span>${pctText} del vaso</span></div></div>`;
    }).join('')
    : '<p class="blank-state">No hay perfil de servido para este modo.</p>';
}

function renderCustomServeEditor() {
  const container = document.getElementById('serve-custom-editor');
  if (!container || !state.activeServeRecipe) return;

  const isCustom = state.activeServeMode === 'custom';
  const liquids = getRecipeLiquidOrder(state.activeServeRecipe);
  const profile = ensureCustomServeProfile(state.activeServeRecipe);
  const total = liquids.reduce((sum, liquid) => sum + Math.max(0, Number(profile[liquid]) || 0), 0);

  container.hidden = !isCustom;
  container.innerHTML = isCustom
    ? `
      <div class="serve-custom-panel">
        <div class="serve-custom-head">
          <div>
            <span class="serve-custom-kicker">Modo Custom</span>
            <h4>Ajusta el reparto del vaso</h4>
          </div>
          <div class="serve-custom-total">${formatCustomPercent(total)}%</div>
        </div>
        <p class="serve-custom-note">Mueve un deslizador y los demás se reajustan para mantener el total en 100%.</p>
        <div class="serve-custom-grid">
          ${liquids.map(liquid => {
            const value = Math.max(0, Number(profile[liquid]) || 0);
            return `
              <div class="serve-custom-row">
                <div class="serve-custom-row-head">
                  <strong>${escapeHtml(liquid)}</strong>
                  <span>${formatCustomPercent(value)}%</span>
                </div>
                <input
                  class="serve-custom-range"
                  type="range"
                  min="0"
                  max="100"
                  step="0.5"
                  aria-label="${escapeHtml(liquid)}"
                  value="${formatCustomPercent(value)}"
                  data-action="adjust-custom-serve-liquid"
                  data-liquid="${escapeHtml(liquid)}"
                >
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `
    : '';
}

function renderServePickers() {
  if (!state.activeServeRecipe) return;
  const recipe = state.activeServeRecipe;
  const availableGlasses = getRecipeGlassOptions(recipe);
  const modeKeys = Object.keys(recipe.serving_modes || {});
  const toRenderModes = [...(modeKeys.length > 0 ? modeKeys : dashboard.constants.SERVE_MODES)];
  if (!toRenderModes.includes('custom')) {
    toRenderModes.push('custom');
  }

  const glassPicker = document.getElementById('serve-glass-picker');
  if (!availableGlasses.length) {
    glassPicker.innerHTML = '<p class="blank-state">No hay vasos disponibles.</p>';
    document.getElementById('serve-mode-picker').innerHTML = '';
    updateServeEstimate();
    return;
  }
  glassPicker.innerHTML = availableGlasses.map(g => {
    const info = getGlassInfo(g);
    const baseMl = Number(info.capacity_ml || 300);
    return `<div class="pick-item ${g === state.activeServeGlass ? 'active' : ''}" data-action="pick-serve-glass" data-glass-key="${g}"><span class="ico">${info.icon || '🥤'}</span><strong>${info.name || info.label || g}</strong><div class="fs-11 text-muted mt-4">${baseMl} mL</div></div>`;
  }).join('');

  const modePicker = document.getElementById('serve-mode-picker');
  modePicker.innerHTML = toRenderModes.map(m => {
    const profile = getServeModeProfile(recipe, m);
    const profileText = m === 'custom'
      ? Object.entries(ensureCustomServeProfile(recipe)).map(([liq, pct]) => `${liq} ${pct}%`).join(' · ')
      : Object.entries(profile).map(([liq, pct]) => `${liq} ${pct}%`).join(' · ');
    const totalMl = computeServeMl(state.activeServeGlass, m);
    const xpValue = computeServeXp(recipe.xp_reward, totalMl, m);
    const label = m === 'custom' ? 'Custom' : m;
    return `<div class="pick-item ${m === state.activeServeMode ? 'active' : ''} ${m === 'custom' ? 'pick-item-custom' : ''}" data-action="pick-serve-mode" data-mode="${m}"><strong class="text-uppercase">${label}</strong><div class="fs-11 text-muted mt-4">${totalMl} ml · ${xpValue} XP</div><div class="fs-11 text-muted mt-4">${profileText || (m === 'custom' ? 'Ajuste manual' : 'Sin perfil')}</div></div>`;
  }).join('');

  renderCustomServeEditor();
  updateServeEstimate();
}

function loadRecipes() {
  return apiGet('/api/drinks/recipes')
    .then(recipes => {
      state.recipesCache = recipes || [];
      const availableLiquids = state.currentTanks.filter(t => t.current_level > 0 && t.name).map(t => t.name.toLowerCase().trim());

      document.getElementById('recipes-list').innerHTML = (recipes || []).map(r => {
        const reqString = r.ingredients || '';
        const reqList = reqString.split(',').map(x => x.trim()).filter(x => x.length > 0);
        const reqs = reqList.map(x => x.toLowerCase());

        let canMake = true;
        if (reqs.length > 0) {
          canMake = reqs.every(reqWord => availableLiquids.some(tankLiq => tankLiq === reqWord || tankLiq.includes(reqWord)));
        }

        const reqHtml = reqList.map(req => {
          const reqNormalized = req.toLowerCase();
          const available = availableLiquids.some(tankLiq => tankLiq === reqNormalized || tankLiq.includes(reqNormalized));
          if (!canMake && !available) {
            return `<span class="missing-ingredient">${escapeHtml(req)}</span>`;
          }
            return `<span class="recipe-ingredient">${escapeHtml(req)}</span>`;
        }).join(', ');

        return `
          <div class="recipe-card ${canMake ? '' : 'disabled'}">
            <div>
                <h3 class="recipe-heading">${r.name}</h3>
                <p class="recipe-desc muted">${r.description}</p>
                <p class="recipe-requirements"><strong class="recipe-require-label">Requiere:</strong> ${reqHtml || '<span class="recipe-ingredient">-</span>'}</p>
            </div>
              <div class="recipe-cta-row">
              <button class="btn" type="button" data-action="open-serve-modal" data-recipe-id="${r.id}">${canMake ? 'Preparar' : 'Faltan líquidos'}</button>
            </div>
          </div>
        `;
      }).join('');
    })
    .catch(() => {});
}

function openServeModal(id) {
  const recipe = getRecipeById(id);
  if (!recipe) return;

  state.activeServeRecipe = recipe;
  const availableGlasses = getRecipeGlassOptions(recipe);
  const modeKeys = Object.keys(recipe.serving_modes || {});

  state.activeServeGlass = availableGlasses[0] || state.activeGlassesCache[0]?.key || 'highball';
  state.activeServeMode = modeKeys.includes('medium') ? 'medium' : (modeKeys[0] || 'medium');
  state.activeServeCustomProfile = normalizeCustomProfile(recipe.serving_modes?.medium || recipe.serving_modes?.[state.activeServeMode] || {}, getRecipeLiquidOrder(recipe));
  state.activeServeCustomLastLiquid = null;

  document.getElementById('serve-title').innerText = `Preparar ${recipe.name}`;
  document.getElementById('serve-desc').innerText = recipe.description || 'Selecciona vaso y modo de servicio.';
  renderServePickers();
  document.getElementById('serve-modal').classList.add('open');
}

function pickServeGlass(glassKey) {
  state.activeServeGlass = glassKey;
  renderServePickers();
}

function pickServeMode(mode) {
  state.activeServeMode = mode;
  if (mode === 'custom') {
    ensureCustomServeProfile(state.activeServeRecipe);
  }
  renderServePickers();
}

function closeServeModal(ev = null) {
  document.getElementById('serve-modal').classList.remove('open');
  state.activeServeRecipe = null;
  state.activeServeCustomProfile = {};
  state.activeServeCustomLastLiquid = null;
}

async function confirmServeDrink() {
  if (!state.activeServeRecipe) return;
  const customProfile = state.activeServeMode === 'custom' ? ensureCustomServeProfile(state.activeServeRecipe) : null;
  await makeDrink(state.activeServeRecipe.id, state.activeServeMode, state.activeServeGlass, customProfile);
  closeServeModal();
}

async function makeDrink(id, servingMode = 'medium', glassType = 'highball', customServingProfile = null) {
  try {
    const payload = { recipe_id: id, serving_mode: servingMode, glass_type: glassType };
    if (servingMode === 'custom' && customServingProfile) {
      payload.custom_serving_profile = customServingProfile;
    }
    const res = await apiPost('/api/drinks/make', payload);
    const mlInfo = res.total_ml ? `\nVolumen: ${res.total_ml} ml` : '';
    alert(`¡Bebida en marcha! 🍹\nHas ganado ${res.xp_earned} XP${mlInfo}`);
    await loadProfile();
    await loadGlobalHistory();
    await loadMyHistory();
  } catch (e) {
    alert('Error al preparar la bebida.');
  }
}

async function loadRanking() {
  const ranking = await apiGet('/api/users/ranking');
  document.getElementById('ranking-list').innerHTML = (ranking || []).map((u, i) => {
    const avatar = u.avatar_url
      ? `<img src="${u.avatar_url}" class="avatar-img recipe-avatar">`
      : `<div class="recipe-avatar-fallback">👤</div>`;

    return `
      <tr>
        <td class="recipe-table-avatar-cell">${avatar}</td>
        <td><strong>#${i + 1}</strong></td>
        <td class="rank-user" title="${u.full_name || u.username}">${u.full_name || u.username}</td>
        <td class="rank-level-cell"><span class="rank-level-badge">LVL ${u.level}</span></td>
        <td><strong>${u.xp}</strong></td>
        <td><strong>${u.total_consumptions ?? 0}</strong></td>
        <td>${u.most_consumed_recipe_name || u.favorite_recipe_name || '-'}</td>
      </tr>
    `;
  }).join('');
}

Object.assign(window, {
  renderGlassSelector,
  toggleGlass,
  renderServingModesEditor,
  collectServingModes,
  getRecipeById,
  updateServeEstimate,
  renderServePickers,
  loadRecipes,
  openServeModal,
  pickServeGlass,
  pickServeMode,
  renderCustomServeEditor,
  updateCustomServeProfile,
  closeServeModal,
  confirmServeDrink,
  makeDrink,
  loadRanking,
});
