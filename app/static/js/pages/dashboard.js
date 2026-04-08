import './dashboard/core.js';
import './dashboard/profile.js';
import './dashboard/machine.js';
import './dashboard/recipes.js';
import './dashboard/admin.js';

let dashboardEventsBound = false;

function toggleSidebar() {
  document.getElementById('sidebar')?.classList.toggle('open');
  document.getElementById('overlay')?.classList.toggle('open');
}

function switchView(viewId, triggerElement = null) {
  document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-menu a').forEach(el => el.classList.remove('active'));

  const view = document.getElementById(`view-${viewId}`);
  if (view) view.classList.add('active');

  triggerElement?.classList.add('active');

  if (window.innerWidth <= 768) toggleSidebar();

  if (viewId === 'ranking') window.loadRanking?.();
  if (viewId === 'admin') window.loadSettings?.();
  if (viewId === 'dashboard') window.loadGlobalHistory?.();
  if (viewId === 'profile') {
    Promise.resolve(window.loadProfile?.()).then(() => window.loadMyHistory?.());
  }
  if (viewId === 'machine') window.pollMachineStatus?.();
}

function handleDashboardClick(event) {
  const actionElement = event.target.closest('[data-action]');
  if (!actionElement) return;

  const { action } = actionElement.dataset;

  if (action.startsWith('close-') && actionElement.classList.contains('modal-backdrop') && event.target !== actionElement) {
    return;
  }

  switch (action) {
    case 'toggle-sidebar':
      event.preventDefault();
      toggleSidebar();
      break;
    case 'switch-view':
      event.preventDefault();
      switchView(actionElement.dataset.view, actionElement);
      break;
    case 'logout':
      event.preventDefault();
      window.cubatronDashboard.api.logout();
      break;
    case 'apply-global-history-filter':
      event.preventDefault();
      window.applyGlobalHistoryFilter?.();
      break;
    case 'change-global-history-page':
      event.preventDefault();
      window.changeGlobalHistoryPage?.(Number(actionElement.dataset.delta || 0));
      break;
    case 'machine-action':
      event.preventDefault();
      window.machineAction?.(actionElement.dataset.machineAction);
      break;
    case 'save-tanks':
      event.preventDefault();
      window.saveTanks?.();
      break;
    case 'reload-admin-panel':
      event.preventDefault();
      window.reloadAdminPanel?.();
      break;
    case 'switch-admin-section':
      event.preventDefault();
      window.switchAdminSection?.(actionElement.dataset.section);
      break;
    case 'toggle-user-form':
      event.preventDefault();
      window.openUserForm?.();
      break;
    case 'close-user-modal':
      window.closeUserForm?.();
      break;
    case 'reset-user-form':
      event.preventDefault();
      window.resetUserForm?.();
      break;
    case 'reset-recipe-form':
      event.preventDefault();
      window.resetRecipeForm?.();
      break;
    case 'toggle-recipe-form':
      event.preventDefault();
      window.openRecipeForm?.();
      break;
    case 'close-recipe-modal':
      window.closeRecipeForm?.(event);
      break;
    case 'reset-glass-form':
      event.preventDefault();
      window.resetGlassForm?.();
      break;
    case 'toggle-glass-form':
      event.preventDefault();
      window.openGlassForm?.();
      break;
    case 'close-glass-modal':
      window.closeGlassForm?.(event);
      break;
    case 'reset-liquid-form':
      event.preventDefault();
      window.resetLiquidForm?.();
      break;
    case 'toggle-liquid-form':
      event.preventDefault();
      window.openLiquidForm?.();
      break;
    case 'close-liquid-modal':
      window.closeLiquidForm?.(event);
      break;
    case 'apply-my-history-filter':
      event.preventDefault();
      window.applyMyHistoryFilter?.();
      break;
    case 'change-my-history-page':
      event.preventDefault();
      window.changeMyHistoryPage?.(Number(actionElement.dataset.delta || 0));
      break;
    case 'close-serve-modal':
      window.closeServeModal?.(event);
      break;
    case 'confirm-serve-drink':
      event.preventDefault();
      window.confirmServeDrink?.();
      break;
    case 'toggle-glass':
      event.preventDefault();
      window.toggleGlass?.(actionElement.dataset.glassKey);
      break;
    case 'pick-serve-glass':
      event.preventDefault();
      window.pickServeGlass?.(actionElement.dataset.glassKey);
      break;
    case 'pick-serve-mode':
      event.preventDefault();
      window.pickServeMode?.(actionElement.dataset.mode);
      break;
    case 'open-serve-modal':
      event.preventDefault();
      window.openServeModal?.(Number(actionElement.dataset.recipeId));
      break;
    case 'delete-liquid':
      event.preventDefault();
      window.deleteLiquid?.(Number(actionElement.dataset.index));
      break;
    case 'edit-liquid':
      event.preventDefault();
      window.editLiquid?.(Number(actionElement.dataset.index));
      break;
    case 'edit-user':
      event.preventDefault();
      window.editUser?.(Number(actionElement.dataset.userId));
      break;
    case 'view-user-activity':
      event.preventDefault();
      window.selectAdminUser?.(Number(actionElement.dataset.userId));
      break;
    case 'archive-user':
      event.preventDefault();
      window.archiveUser?.(Number(actionElement.dataset.userId), actionElement.dataset.archived === 'true');
      break;
    case 'purge-user':
      event.preventDefault();
      window.purgeUser?.(Number(actionElement.dataset.userId));
      break;
    case 'edit-glass':
      event.preventDefault();
      window.editGlass?.(Number(actionElement.dataset.glassId));
      break;
    case 'delete-glass':
      event.preventDefault();
      window.deleteGlass?.(Number(actionElement.dataset.glassId));
      break;
    case 'toggle-ingredient':
      event.preventDefault();
      window.toggleIngredient?.(actionElement.dataset.ingredientName);
      break;
    case 'edit-recipe':
      event.preventDefault();
      window.editRecipe?.(Number(actionElement.dataset.recipeId));
      break;
    case 'delete-recipe':
      event.preventDefault();
      window.deleteRecipe?.(Number(actionElement.dataset.recipeId));
      break;
    default:
      break;
  }
}

function handleDashboardInput(event) {
  const actionElement = event.target.closest('[data-action]');
  if (!actionElement) return;

  const { action } = actionElement.dataset;

  switch (action) {
    case 'adjust-custom-serve-liquid':
      event.preventDefault();
      window.updateCustomServeProfile?.(actionElement.dataset.liquid, actionElement.value);
      break;
    default:
      break;
  }
}

function bindDashboardEvents() {
  if (dashboardEventsBound) return;
  dashboardEventsBound = true;

  document.addEventListener('click', handleDashboardClick);
  document.addEventListener('input', handleDashboardInput);

  const formBindings = [
    ['user-form', window.saveUser],
    ['add-recipe-form', window.addRecipe],
    ['glass-form', window.saveGlass],
    ['liquid-form', window.saveLiquid],
    ['settings-form', window.saveSettings],
    ['profile-form', window.updateProfile],
    ['password-form', window.updatePassword],
  ];

  formBindings.forEach(([id, handler]) => {
    document.getElementById(id)?.addEventListener('submit', (event) => {
      handler?.(event);
    });
  });

  document.getElementById('gl-name')?.addEventListener('input', () => window.syncGlassKey?.());
  document.getElementById('admin-user-search')?.addEventListener('input', () => window.renderAdminUsers?.());
}

function initDashboard() {
  if (!window.cubatronDashboard.api.getToken()) {
    window.location.href = '/';
    return;
  }

  const { state } = window.cubatronDashboard;
  bindDashboardEvents();

  const safeCall = (fn, label) => Promise.resolve()
    .then(fn)
    .catch(err => {
      if (String(err) !== 'Error: unauthorized') {
        console.error(`Error ${label}`, err);
      }
    });

  safeCall(
    () => window.cubatronDashboard.api.apiGet('/api/admin/settings')
      .then(settings => {
        state.systemSettings = settings || state.systemSettings;
      }),
    'cargando ajustes'
  );

  safeCall(() => window.loadProfile(), 'cargando perfil');
  safeCall(() => window.loadActiveGlasses(), 'cargando vasos');
  safeCall(() => window.pollMachineStatus(), 'cargando estado de maquina');
  safeCall(() => window.loadRecipes(), 'cargando recetas');
  safeCall(() => window.loadGlobalHistory(), 'cargando historial global');
  safeCall(() => window.loadMyHistory(), 'cargando historial personal');

  window.setInterval(window.pollMachineStatus, state.systemSettings.poll_status || 3000);
  window.setInterval(() => {
    if (!document.querySelector('select:focus')) window.renderTanks();
  }, state.systemSettings.poll_tanks || 10000);
}

Object.assign(window, {
  initDashboard,
  toggleSidebar,
  switchView,
});

document.addEventListener('DOMContentLoaded', initDashboard);
