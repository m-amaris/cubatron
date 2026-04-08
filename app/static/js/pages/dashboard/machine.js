const dashboard = window.cubatronDashboard;
const state = dashboard.state;
const { apiGet, apiPost } = dashboard.api;

async function pollMachineStatus() {
  try {
    const data = await apiGet('/api/machine/status');
    document.getElementById('machine-status').className = `status-indicator compact status-${data.status}`;
    document.getElementById('status-text').innerText = data.status;

    if (data.drinks_24h !== undefined) {
      document.getElementById('status-drinks').innerText = data.drinks_24h;
    }

    const incomingTanks = data.tanks || [];
    const newSignature = JSON.stringify(incomingTanks.map(t => [t.id, t.name || '', t.current_level || 0, t.current_ml || 0]));
    const changed = newSignature !== state.tankSignature;

    if (!document.querySelector('select:focus') && !document.querySelector('input:focus')) {
      state.currentTanks = incomingTanks;
      renderTanks();
    }

    if (changed) {
      state.tankSignature = newSignature;
      await loadRecipes();
    }
  } catch (e) {}
}

function renderTanks() {
  const container = document.getElementById('tanks-list');
  if (container.innerHTML.includes('focus')) return;

  const liquids = state.systemSettings.liquids || [];
  container.innerHTML = state.currentTanks.map((t, i) => {
    const options = liquids.map(l => `<option value="${l.name}" ${t.name === l.name ? 'selected' : ''}>${l.name}</option>`).join('');

    return `
      <div class="tank-item">
        <div class="tank-header">
          <strong class="text-primary">Depósito ${t.id}</strong>
          <button class="btn btn-small btn-secondary" type="button" data-action="machine-action" data-machine-action="purge_tank_${t.id}">Purgar</button>
        </div>
        <div class="grid-1-100">
          <select class="form-control" id="tank-name-${i}">
            <option value="">-- Vacío / Seleccionar --</option>
            ${options}
          </select>
          <div class="flex-align-center-gap-8">
            <input type="number" class="form-control" id="tank-level-${i}" value="${t.current_level || 0}">
            <span>%</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function saveTanks() {
  const updates = state.currentTanks.map((t, i) => {
    const selectedName = document.getElementById(`tank-name-${i}`).value || '';
    const liquidInfo = (state.systemSettings.liquids || []).find(l => l.name === selectedName);
    const levelVal = parseInt(document.getElementById(`tank-level-${i}`).value) || 0;

    return {
      id: t.id,
      name: selectedName,
      liquid_type: liquidInfo ? liquidInfo.type : 'mixer',
      current_ml: levelVal,
    };
  });

  try {
    await apiPost('/api/machine/tanks/update', updates);
    alert('Depósitos guardados con éxito');
    pollMachineStatus();
    loadRecipes();
  } catch (e) {
    alert('Error al guardar.');
  }
}

async function machineAction(action) {
  await apiPost(`/api/machine/action/${action}`, {});
  pollMachineStatus();
}

async function loadActiveGlasses() {
  try {
    const glasses = await apiGet('/api/drinks/glasses');
    state.activeGlassesCache = glasses || [];
  } catch (e) {
    state.activeGlassesCache = [];
  }

  if (state.selectedGlasses.length === 0 || !state.selectedGlasses.some(key => state.activeGlassesCache.some(g => g.key === key))) {
    state.selectedGlasses = state.activeGlassesCache.length > 0 ? [state.activeGlassesCache[0].key] : ['highball'];
  }

  renderGlassSelector();
  if (state.activeServeRecipe) renderServePickers();
}

Object.assign(window, {
  pollMachineStatus,
  renderTanks,
  saveTanks,
  machineAction,
  loadActiveGlasses,
});
