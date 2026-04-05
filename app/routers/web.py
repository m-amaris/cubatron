from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def login_page():
    html = """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Cubatron – Login</title>
      <style>
        body { margin:0; font-family: Arial, sans-serif; background:#0f172a; color:#e5e7eb; }
        main { min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
        .card { background:#1e293b; padding:24px; border-radius:16px; width:100%; max-width:380px; box-shadow:0 10px 30px rgba(0,0,0,.3); }
        h1 { margin:0 0 12px; color:#22c55e; }
        p { color:#cbd5e1; }
        input, button {
          width:100%; padding:12px; margin:8px 0; border-radius:10px; border:none; font-size:16px;
        }
        input { background:#0f172a; color:#fff; border:1px solid #334155; }
        button { background:#22c55e; color:#052e16; font-weight:700; cursor:pointer; }
        #loginMsg { min-height:1.5em; color:#f97316; }
      </style>
      <script>
        const tokenKey = "cubatron_token";
        async function doLogin(ev){
          ev.preventDefault();
          const username = document.getElementById("username").value;
          const password = document.getElementById("password").value;

          const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username, password})
          });

          const data = await res.json().catch(() => ({}));

          if(!res.ok || !data.access_token){
            document.getElementById("loginMsg").innerText = data.detail || "Login incorrecto";
            return;
          }

          sessionStorage.setItem(tokenKey, data.access_token);
          window.location.href = "/dashboard";
        }
      </script>
    </head>
    <body>
      <main>
        <div class="card">
          <h1>Cubatron</h1>
          <p>Inicia sesión para preparar tu cubata.</p>
          <form onsubmit="doLogin(event)">
            <input type="text" id="username" placeholder="Usuario" required>
            <input type="password" id="password" placeholder="Contraseña" required>
            <button type="submit">Entrar</button>
          </form>
          <p id="loginMsg"></p>
        </div>
      </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    html = """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Cubatron – Dashboard</title>
      <style>
        :root {
          --bg: #0f172a;
          --surface: #1e293b;
          --surface-2: #0b1220;
          --text: #e5e7eb;
          --muted: #94a3b8;
          --green: #22c55e;
          --green-dark: #052e16;
          --border: #334155;
          --orange: #f97316;
        }
        * { box-sizing: border-box; }
        body { margin:0; font-family: Arial, sans-serif; background:var(--bg); color:var(--text); }
        header {
          display:flex; justify-content:space-between; align-items:center; gap:16px;
          padding:24px; flex-wrap:wrap; border-bottom:1px solid #1f2937;
        }
        h1,h2,h3 { margin:0 0 12px; }
        .container { max-width:1200px; margin:0 auto; padding:24px; }
        .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:20px; }
        .card {
          background:var(--surface); border-radius:16px; padding:20px;
          box-shadow:0 10px 24px rgba(0,0,0,.18);
        }
        .wide { grid-column:1 / -1; }
        .btn, button {
          display:inline-block; background:var(--green); color:var(--green-dark);
          padding:10px 14px; border:none; border-radius:10px; text-decoration:none;
          font-weight:700; cursor:pointer; margin-right:8px; margin-top:8px;
        }
        .btn.secondary { background:#334155; color:#e5e7eb; }
        .muted { color:var(--muted); }
        .pill {
          display:inline-block; padding:6px 10px; border-radius:999px;
          background:#132235; color:#93c5fd; font-size:14px; margin-right:8px;
        }
        .list { display:grid; gap:12px; }
        .item {
          background:var(--surface-2); border:1px solid var(--border);
          border-radius:12px; padding:14px;
        }
        .recipe-title { display:flex; justify-content:space-between; gap:12px; align-items:center; flex-wrap:wrap; }
        .small { font-size:14px; }
        .ok { color:#86efac; }
        .warn { color:var(--orange); }
        .kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; }
        .kpi { background:var(--surface-2); border-radius:12px; padding:14px; border:1px solid var(--border); }
        pre {
          white-space:pre-wrap; word-break:break-word; background:var(--surface-2);
          padding:12px; border-radius:12px; border:1px solid var(--border);
        }
      </style>
    </head>
    <body>
      <header>
        <div>
          <h1>Cubatron Dashboard</h1>
          <div class="muted">V1 – Usuario, recetas, máquina e inicio admin</div>
        </div>
        <div>
          <a class="btn secondary" href="/docs">Swagger</a>
          <button onclick="logout()">Salir</button>
        </div>
      </header>

      <main class="container">
        <section class="grid">
          <article class="card">
            <h2>Perfil</h2>
            <div id="profile" class="muted">Cargando perfil...</div>
          </article>

          <article class="card">
            <h2>Estado máquina</h2>
            <div id="machine" class="muted">Cargando estado...</div>
            <div>
              <button onclick="machineAction('prime')">Cebar</button>
              <button onclick="machineAction('purge')">Purgar</button>
              <button onclick="machineAction('clean')">Limpiar</button>
            </div>
            <div id="machineMsg" class="small muted"></div>
          </article>

          <article class="card">
            <h2>Admin</h2>
            <div id="admin" class="muted">Cargando overview...</div>
          </article>

          <article class="card wide">
            <h2>Recetas disponibles</h2>
            <div id="recipes" class="list muted">Cargando recetas...</div>
          </article>

          <article class="card wide">
            <h2>Mis últimas consumiciones</h2>
            <div id="history" class="list muted">Cargando historial...</div>
          </article>
        </section>
      </main>

      <script>
        const tokenKey = "cubatron_token";

        function getToken() {
          return sessionStorage.getItem(tokenKey);
        }

        function authHeaders() {
          const token = getToken();
          return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
          };
        }

        function logout() {
          sessionStorage.removeItem(tokenKey);
          window.location.href = "/";
        }

        async function apiGet(url, needsAuth = false) {
          const options = {};
          if (needsAuth) options.headers = authHeaders();
          const res = await fetch(url, options);
          if (!res.ok) throw new Error(url + " -> " + res.status);
          return await res.json();
        }

        async function apiPost(url, body = null, needsAuth = false) {
          const options = { method: "POST" };
          if (needsAuth) options.headers = authHeaders();
          if (body) options.body = JSON.stringify(body);
          const res = await fetch(url, options);
          const data = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(data.detail || (url + " -> " + res.status));
          return data;
        }

        function renderProfile(user) {
          const el = document.getElementById("profile");
          el.innerHTML = `
            <div class="kpis">
              <div class="kpi"><div class="small muted">Nombre</div><strong>${user.full_name || "-"}</strong></div>
              <div class="kpi"><div class="small muted">Usuario</div><strong>${user.username}</strong></div>
              <div class="kpi"><div class="small muted">Rol</div><strong>${user.role}</strong></div>
              <div class="kpi"><div class="small muted">Nivel</div><strong>${user.level}</strong></div>
              <div class="kpi"><div class="small muted">XP</div><strong>${user.xp}</strong></div>
              <div class="kpi"><div class="small muted">Mix favorito</div><strong>${user.favorite_mix || "-"}</strong></div>
            </div>
          `;
        }

        function renderMachine(data) {
          const tanks = (data.tanks || []).map(t => `
            <div class="item">
              <strong>${t.name || t.liquid_name || "Depósito"}</strong><br>
              <span class="small muted">Nivel: ${t.level_ml ?? t.current_level ?? "?"}</span>
            </div>
          `).join("");

          document.getElementById("machine").innerHTML = `
            <p><span class="pill">Estado: ${data.status}</span><span class="pill">Temp: ${data.temperature} ºC</span></p>
            <div class="list">${tanks || '<div class="item">No hay depósitos cargados.</div>'}</div>
          `;
        }

        function renderRecipes(recipes) {
          const el = document.getElementById("recipes");
          if (!recipes.length) {
            el.innerHTML = '<div class="item">No hay recetas activas.</div>';
            return;
          }

          el.innerHTML = recipes.map(r => `
            <div class="item">
              <div class="recipe-title">
                <div>
                  <strong>${r.name}</strong><br>
                  <span class="small muted">${r.description || "Sin descripción"}</span>
                </div>
                <div>
                  <button onclick="makeDrink(${r.id})">Preparar</button>
                </div>
              </div>
            </div>
          `).join("");
        }

        function renderHistory(items) {
          const el = document.getElementById("history");
          if (!items.length) {
            el.innerHTML = '<div class="item">Todavía no hay consumiciones registradas.</div>';
            return;
          }

          el.innerHTML = items.map(d => `
            <div class="item">
              <strong>Receta #${d.recipe_id}</strong><br>
              <span class="small muted">Acción: ${d.action || "make_drink"}</span><br>
              <span class="small muted">Fecha: ${d.created_at || "-"}</span>
            </div>
          `).join("");
        }

        function renderAdmin(data) {
          const el = document.getElementById("admin");
          el.innerHTML = `
            <div class="kpis">
              <div class="kpi"><div class="small muted">Usuarios</div><strong>${data.users}</strong></div>
              <div class="kpi"><div class="small muted">Recetas</div><strong>${data.recipes}</strong></div>
              <div class="kpi"><div class="small muted">Depósitos</div><strong>${data.tanks}</strong></div>
              <div class="kpi"><div class="small muted">Eventos</div><strong>${data.events}</strong></div>
            </div>
          `;
        }

        async function makeDrink(recipeId) {
          try {
            const data = await apiPost("/api/drinks/make", { recipe_id: recipeId }, true);
            alert("Bebida preparada correctamente");
            await loadHistory();
            await loadProfile();
          } catch (e) {
            alert("Error al preparar bebida: " + e.message);
          }
        }

        async function machineAction(action) {
          const msg = document.getElementById("machineMsg");
          msg.innerText = "Ejecutando...";
          try {
            const data = await apiPost("/api/machine/" + action, null, false);
            msg.innerText = data.message || "Acción completada";
            await loadMachine();
          } catch (e) {
            msg.innerText = "Error: " + e.message;
          }
        }

        async function loadProfile() {
          try {
            const user = await apiGet("/api/users/me", true);
            renderProfile(user);
            window.__user = user;
          } catch (e) {
            document.getElementById("profile").innerHTML = '<div class="warn">No se pudo cargar el perfil.</div>';
          }
        }

        async function loadMachine() {
          try {
            const data = await apiGet("/api/machine/status");
            renderMachine(data);
          } catch (e) {
            document.getElementById("machine").innerHTML = '<div class="warn">No se pudo cargar el estado de la máquina.</div>';
          }
        }

        async function loadRecipes() {
          try {
            const data = await apiGet("/api/drinks/recipes");
            renderRecipes(data);
          } catch (e) {
            document.getElementById("recipes").innerHTML = '<div class="warn">No se pudieron cargar las recetas.</div>';
          }
        }

        async function loadHistory() {
          try {
            const data = await apiGet("/api/users/me/drinks", true);
            renderHistory(data);
          } catch (e) {
            document.getElementById("history").innerHTML = '<div class="warn">No se pudo cargar el historial.</div>';
          }
        }

        async function loadAdmin() {
          try {
            const user = window.__user;
            if (!user || user.role !== "admin") {
              document.getElementById("admin").innerHTML = '<div class="muted">Panel admin no disponible para este usuario.</div>';
              return;
            }
            const data = await apiGet("/api/admin/overview");
            renderAdmin(data);
          } catch (e) {
            document.getElementById("admin").innerHTML = '<div class="warn">No se pudo cargar el overview admin.</div>';
          }
        }

        async function init() {
          const token = getToken();
          if (!token) {
            window.location.href = "/";
            return;
          }

          await loadProfile();
          await Promise.all([
            loadMachine(),
            loadRecipes(),
            loadHistory()
          ]);
          await loadAdmin();
        }

        window.onload = init;
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)
