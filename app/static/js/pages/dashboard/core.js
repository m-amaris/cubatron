const dashboard = window.cubatronDashboard || (window.cubatronDashboard = {});

const state = dashboard.state || (dashboard.state = {
	currentUser: null,
	currentTanks: [],
	systemSettings: { poll_status: 3000, poll_tanks: 10000, poll_history: 30000, liquids: [] },
	selectedIngredients: [],
	selectedGlasses: ['highball'],
	recipesCache: [],
	adminRecipesCache: [],
	activeGlassesCache: [],
	adminGlassesCache: [],
	adminOverview: {},
	adminUsersCache: [],
	adminSelectedUserId: null,
	adminActiveSection: 'users',
	adminUserActivity: { user: null, items: [] },
	tankSignature: '',
	activeServeRecipe: null,
	activeServeGlass: 'highball',
	activeServeMode: 'medium',
	activeServeCustomProfile: {},
	activeServeCustomLastLiquid: null,
	globalHistoryState: { page: 1, pageSize: 8, q: '' },
	myHistoryState: { page: 1, pageSize: 8, q: '' },
});

const constants = dashboard.constants || (dashboard.constants = {
	DEFAULT_GLASS_CATALOG: {
		highball: { label: 'Highball', icon: '🥤' },
		rocks: { label: 'Rocks', icon: '🥃' },
		coupe: { label: 'Coupe', icon: '🍸' },
		hurricane: { label: 'Hurricane', icon: '🍹' },
		shot: { label: 'Shot', icon: '🧪' },
	},
	MODE_XP_MULTIPLIER: { low: 0.9, medium: 1.0, high: 1.2, extreme: 1.4, custom: 1.0 },
	SERVE_MODES: ['low', 'medium', 'high', 'extreme'],
	ACCENT_PALETTE: {
		emerald: { primary: '#10b981', hover: '#059669' },
		blue: { primary: '#3b82f6', hover: '#2563eb' },
		orange: { primary: '#f97316', hover: '#ea580c' },
		rose: { primary: '#f43f5e', hover: '#e11d48' },
		slate: { primary: '#64748b', hover: '#475569' },
	},
});

function applyThemePreferences(themeMode = 'dark', accentColor = 'emerald') {
	const root = document.documentElement;
	const accent = constants.ACCENT_PALETTE[accentColor] || constants.ACCENT_PALETTE.emerald;

	if (themeMode === 'light') {
		root.style.setProperty('--bg', '#f1f5f9');
		root.style.setProperty('--surface', '#ffffff');
		root.style.setProperty('--surface-2', '#e2e8f0');
		root.style.setProperty('--text', '#0f172a');
		root.style.setProperty('--muted', '#475569');
		root.style.setProperty('--border', '#cbd5e1');
	} else {
		root.style.setProperty('--bg', '#0f172a');
		root.style.setProperty('--surface', '#1e293b');
		root.style.setProperty('--surface-2', '#334155');
		root.style.setProperty('--text', '#f8fafc');
		root.style.setProperty('--muted', '#94a3b8');
		root.style.setProperty('--border', '#334155');
	}

	root.style.setProperty('--primary', accent.primary);
	root.style.setProperty('--primary-hover', accent.hover);
}

function escapeHtml(value) {
	return String(value || '')
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#39;');
}

function formatRelativeTime(isoValue) {
	if (!isoValue) return '';
	const raw = String(isoValue).trim();
	const hasTz = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw);
	const normalized = hasTz ? raw : `${raw}Z`;
	const date = new Date(normalized);
	if (Number.isNaN(date.getTime())) return String(isoValue);

	const diffMs = date.getTime() - Date.now();
	const absMs = Math.abs(diffMs);
	const minute = 60 * 1000;
	const hour = 60 * minute;
	const day = 24 * hour;
	const month = 30 * day;
	const year = 365 * day;

	let value = 0;
	let unit = 'minute';

	if (absMs < minute) {
		return 'hace unos segundos';
	} else if (absMs < hour) {
		value = Math.round(diffMs / minute);
		unit = 'minute';
	} else if (absMs < day) {
		value = Math.round(diffMs / hour);
		unit = 'hour';
	} else if (absMs < month) {
		value = Math.round(diffMs / day);
		unit = 'day';
	} else if (absMs < year) {
		value = Math.round(diffMs / month);
		unit = 'month';
	} else {
		value = Math.round(diffMs / year);
		unit = 'year';
	}

	return new Intl.RelativeTimeFormat('es', { numeric: 'auto' }).format(value, unit);
}

function normalizeModeMap(rawModes, selected) {
	const safe = rawModes && typeof rawModes === 'object' ? rawModes : {};
	const out = {};
	constants.SERVE_MODES.forEach(mode => {
		const current = safe[mode] && typeof safe[mode] === 'object' ? safe[mode] : {};
		out[mode] = {};
		selected.forEach(liq => {
			const num = Number(current[liq]);
			out[mode][liq] = Number.isFinite(num) ? num : 0;
		});
	});
	return out;
}

function slugifyGlassKey(value) {
	return String(value || '')
		.trim()
		.toLowerCase()
		.replace(/[^a-z0-9_-]+/g, '-')
		.replace(/-{2,}/g, '-')
		.replace(/^-+|-+$/g, '')
		.slice(0, 32) || 'glass';
}

function getGlassCatalog() {
	const source = state.activeGlassesCache.length > 0 ? state.activeGlassesCache : state.adminGlassesCache;
	const catalog = {};
	source.forEach(glass => {
		catalog[glass.key] = glass;
	});
	if (Object.keys(catalog).length === 0) {
		return constants.DEFAULT_GLASS_CATALOG;
	}
	return catalog;
}

function getGlassInfo(glassKey) {
	const catalog = getGlassCatalog();
	const glass = catalog[glassKey];
	if (glass) return glass;
	return constants.DEFAULT_GLASS_CATALOG[glassKey] || { key: glassKey, name: glassKey, icon: '🥤', capacity_ml: 300 };
}

function getRecipeGlassOptions(recipe) {
	const availableKeys = new Set((state.activeGlassesCache.length > 0 ? state.activeGlassesCache : state.adminGlassesCache).filter(g => g.enabled !== false).map(g => g.key));
	const fromRecipe = Array.isArray(recipe?.glass_options) ? recipe.glass_options : [];
	const filtered = fromRecipe.filter(key => availableKeys.has(key));
	if (filtered.length > 0) return filtered;
	const fallback = Array.from(availableKeys);
	return fallback.length > 0 ? fallback : Object.keys(constants.DEFAULT_GLASS_CATALOG);
}

function computeServeXp(baseXp, capacityMl, modeKey) {
	const glassMult = Math.max(0.6, Math.min(2.2, Number(capacityMl || 300) / 300));
	const modeMult = constants.MODE_XP_MULTIPLIER[modeKey] || 1.0;
	return Math.max(1, Math.round(Number(baseXp || 0) * glassMult * modeMult));
}

function buildLiquidBreakdown(profile, totalMl) {
	const entries = Object.entries(profile || {})
		.map(([liq, rawPct]) => [String(liq), Math.max(0, Number(rawPct) || 0)]);
	const pctSum = entries.reduce((sum, [, pct]) => sum + pct, 0);
	if (entries.length === 0 || pctSum <= 0) return [];

	let allocated = 0;
	return entries.map(([liq, pct], index) => {
		const ml = index === entries.length - 1
			? Math.max(0, totalMl - allocated)
			: Math.round(totalMl * (pct / pctSum));
		allocated += ml;
		return { liquid: liq, pct: Number(pct.toFixed(2)), ml };
	});
}

function getToken() {
	return sessionStorage.getItem('cubatron_token');
}

function logout() {
	sessionStorage.removeItem('cubatron_token');
	window.location.href = '/';
}

function authHeaders() {
	const token = getToken();
	return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiGet(url) {
	const res = await fetch(url, { headers: authHeaders() });
	if (res.status === 401) {
		logout();
		throw new Error('unauthorized');
	}
	if (!res.ok) {
		let payload = null;
		try {
			payload = await res.json();
		} catch (e) {
			payload = await res.text().catch(() => '');
		}
		const detail = payload && typeof payload === 'object' ? (payload.detail || payload.message || payload.error) : payload;
		throw new Error(typeof detail === 'string' && detail.trim() ? detail : `Error ${res.status}`);
	}
	return await res.json();
}

async function apiPost(url, body) {
	const res = await fetch(url, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json', ...authHeaders() },
		body: JSON.stringify(body),
	});
	if (res.status === 401) {
		logout();
		throw new Error('unauthorized');
	}
	if (!res.ok) {
		let payload = null;
		try {
			payload = await res.json();
		} catch (e) {
			payload = await res.text().catch(() => '');
		}

		const detail = payload && typeof payload === 'object' ? (payload.detail || payload.message || payload.error) : payload;
		let message = `Error ${res.status}`;
		if (Array.isArray(detail)) {
			message = detail
				.map(item => {
					const path = Array.isArray(item?.loc) ? item.loc.join('.') : '';
					const suffix = path ? ` (${path})` : '';
					return `${item?.msg || 'Error de validación'}${suffix}`;
				})
				.join('; ');
		} else if (typeof detail === 'string' && detail.trim()) {
			message = detail;
		}
		throw new Error(message);
	}
	return await res.json();
}

dashboard.state = state;
dashboard.constants = constants;
dashboard.utils = {
	applyThemePreferences,
	escapeHtml,
	formatRelativeTime,
	normalizeModeMap,
	slugifyGlassKey,
	getGlassCatalog,
	getGlassInfo,
	getRecipeGlassOptions,
	computeServeXp,
	buildLiquidBreakdown,
};
dashboard.api = { getToken, logout, authHeaders, apiGet, apiPost };
