let token = sessionStorage.getItem("token");

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (token) headers["Authorization"] = "Bearer " + token;
  if (!headers["Content-Type"] && options.body) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { ...options, headers });
  return res.json();
}

const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const res = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    if (res.access_token) {
      sessionStorage.setItem("token", res.access_token);
      window.location.href = "/dashboard";
    } else {
      document.getElementById("loginMsg").innerText = "Login incorrecto";
    }
  });
}

async function loadDashboard() {
  const meBox = document.getElementById("me");
  if (meBox) {
    const me = await api("/api/users/me");
    meBox.innerHTML = `<p>${me.full_name}</p><p>XP: ${me.xp}</p><p>Nivel: ${me.level}</p>`;
  }

  const drinksBox = document.getElementById("drinks");
  if (drinksBox) {
    const drinks = await api("/api/users/me/drinks");
    drinksBox.innerHTML = drinks.map(d => `<p>#${d.id} · ${d.action} · ${d.created_at}</p>`).join("");
  }

  const recipesBox = document.getElementById("recipes");
  if (recipesBox) {
    const recipes = await api("/api/drinks/recipes");
    recipesBox.innerHTML = recipes.map(r =>
      `<button onclick="makeDrink(${r.id})">${r.name} (${r.spirit_ml}+${r.mixer_ml} ml)</button>`
    ).join("");
  }

  const machineBox = document.getElementById("machine");
  if (machineBox) {
    const machine = await api("/api/machine/status");
    machineBox.innerHTML = `<p>Estado: ${machine.status}</p><p>Temp: ${machine.temperature}°C</p>` +
      machine.tanks.map(t => `<p>${t.name}: ${t.content} (${t.current_ml}/${t.capacity_ml} ml)</p>`).join("");
  }

  const adminBox = document.getElementById("adminOverview");
  if (adminBox) {
    const overview = await api("/api/admin/overview");
    adminBox.innerHTML = `<p>Usuarios: ${overview.users}</p><p>Recetas: ${overview.recipes}</p><p>Tanques: ${overview.tanks}</p><p>Eventos: ${overview.events}</p>`;
  }
}

async function makeDrink(recipeId) {
  const res = await api("/api/drinks/make", {
    method: "POST",
    body: JSON.stringify({ recipe_id: recipeId })
  });
  alert(res.message || "Acción enviada");
  loadDashboard();
}

async function purgeMachine() {
  const res = await api("/api/machine/purge", { method: "POST" });
  alert(res.message);
}
async function primeMachine() {
  const res = await api("/api/machine/prime", { method: "POST" });
  alert(res.message);
}
async function cleanMachine() {
  const res = await api("/api/machine/clean", { method: "POST" });
  alert(res.message);
}

loadDashboard();
