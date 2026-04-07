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
        body { margin:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#111827; color:#f3f4f6; }
        main { min-height:100vh; display:flex; align-items:center; justify-content:center; }
        .card { background:#1f2937; padding:32px; border-radius:12px; width:100%; max-width:400px; box-shadow:0 15px 35px rgba(0,0,0,.5); }
        h1 { margin-top:0; color:#10b981; font-size: 28px; text-align: center; }
        input, button { width:100%; padding:14px; margin:8px 0; border-radius:8px; border:none; font-size:16px; box-sizing:border-box;}
        input { background:#374151; color:white; }
        button { background:#10b981; color:#111827; font-weight:bold; cursor:pointer; transition: background 0.2s;}
        button:hover { background: #059669; }
        #loginMsg { min-height:1.5em; color:#ef4444; text-align:center; margin-top: 10px;}
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
          <p style="text-align: center; color: #9ca3af; margin-bottom: 24px;">Inicia sesión para preparar tu bebida.</p>
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
          --bg: #0f172a; --surface: #1e293b; --surface-2: #334155; --text: #f8fafc;
          --muted: #94a3b8; --primary: #10b981; --primary-hover: #059669;
          --border: #334155; --danger: #ef4444; --warning: #f59e0b; --admin-color: #f97316;
          --sidebar-width: 280px;
        }
        body { margin:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:var(--bg); color:var(--text); overflow-x: hidden;}
        * { box-sizing: border-box; }
        
        .app-container { display: flex; min-height: 100vh; }
        
        .sidebar {
            width: var(--sidebar-width); background: var(--surface); border-right: 1px solid var(--border);
            display: flex; flex-direction: column; transition: transform 0.3s ease;
            position: fixed; height: 100vh; z-index: 50;
        }
        .sidebar-header { padding: 30px 20px; text-align: center; border-bottom: 1px solid var(--border); }
        .sidebar-header h1 { margin: 0 0 24px 0; color: var(--primary); font-size: 26px; }
        
        .nav-menu { display: flex; flex-direction: column; padding: 20px 0; flex-grow: 1; }
        .nav-menu a { padding: 16px 24px; color: var(--muted); text-decoration: none; font-weight: 600; cursor: pointer; transition: 0.2s; text-transform: uppercase; letter-spacing: 1px; font-size: 14px;}
        .nav-menu a:hover { background: var(--surface-2); color: var(--text); }
        .nav-menu a.active { border-left: 4px solid var(--primary); color: var(--text); background: rgba(16, 185, 129, 0.1); box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.08); }
        .nav-menu a#nav-admin { color: var(--admin-color); font-weight: 800; }
        .nav-menu a#nav-admin.active { border-left-color: var(--admin-color); background: rgba(249, 115, 22, 0.1); color: var(--text); box-shadow: inset 0 0 0 1px rgba(249, 115, 22, 0.08); }
        
        .main-content { flex-grow: 1; margin-left: var(--sidebar-width); padding: 32px; transition: margin-left 0.3s ease; width: 100%;}
        
        .mobile-topbar { display: none; background: var(--surface); padding: 16px; border-bottom: 1px solid var(--border); align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 40;}
        .hamburger { background: none; border: none; color: var(--text); font-size: 24px; cursor: pointer; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 45; }

        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .main-content { margin-left: 0; padding: 16px; }
            .mobile-topbar { display: flex; }
            .overlay.open { display: block; }
        }

        .view-section { display: none; animation: fadeIn 0.3s; }
        .view-section.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .card { background:var(--surface); border-radius:12px; padding:24px; box-shadow:0 4px 6px -1px rgba(0,0,0,.3); margin-bottom: 24px; border: 1px solid var(--border);}
        .card h2 { margin-top:0; font-size: 20px; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 20px;}
        
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
        
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 14px; color: var(--muted);}
        .form-control { width: 100%; padding: 12px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; }
        
        .btn { display:inline-block; background:var(--primary); color:#000; padding:12px 16px; border:none; border-radius:8px; font-weight:bold; cursor:pointer; text-align:center; transition:0.2s;}
        .btn:hover { background: var(--primary-hover); }
        .btn-small { padding: 6px 12px; font-size: 14px; }
        .btn-secondary { background: var(--surface-2); color: var(--text); }
        .btn-danger { background: var(--danger); color: var(--text); }

        .status-indicator { display: inline-flex; align-items: center; gap: 8px; font-weight: bold; padding: 8px 16px; border-radius: 20px; background: var(--surface-2);}
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-indicator.compact { padding: 6px 12px; border-radius: 14px; font-size: 13px; gap: 6px; }
        .status-indicator.compact .status-dot { width: 10px; height: 10px; }
        .status-24h-box { background:var(--surface-2); padding:8px 12px; border-radius:8px; border:1px solid var(--border); min-width: 150px; }
        .status-24h-label { margin:0; font-size:11px; color:var(--muted); line-height:1.2; }
        .status-24h-value { color:var(--text); font-size:16px; display:block; text-align:right; line-height:1.1; }
        .status-ONLINE .status-dot { background: var(--primary); box-shadow: 0 0 8px var(--primary);}
        .status-BUSY .status-dot { background: var(--warning); box-shadow: 0 0 8px var(--warning); animation: pulse 1s infinite;}
        .status-OFFLINE .status-dot { background: var(--danger); }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

        .camera-feed { width: 100%; height: 300px; background: #000; border-radius: 8px; display:flex; align-items:center; justify-content:center; color: #fff; position: relative; overflow:hidden; border: 1px solid var(--border);}
        
        .tank-item { background: var(--bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border); }
        
        .recipe-card { border: 1px solid var(--border); border-radius: 12px; padding: 20px; background: var(--bg); display:flex; flex-direction:column; justify-content:space-between; transition: 0.2s;}
        .recipe-card.disabled { opacity: 0.65; pointer-events: none; }
        .recipe-card.disabled .btn { display: none; }
        .missing-ingredient { color: var(--warning); font-weight: 700; }
        .history-item { background: var(--surface-2); padding: 16px; border-radius: 8px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
        .history-user { display:flex; align-items:flex-start; gap:10px; min-width:0; }
        .history-avatar { width:34px; height:34px; border-radius:50%; object-fit:cover; border:1px solid var(--border); background:var(--bg); flex:0 0 auto; }
        .history-avatar-fallback { width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:var(--bg); border:1px solid var(--border); font-size:15px; flex:0 0 auto; }
        .history-main { min-width: 0; flex: 1; }
        .history-title { color: var(--text); font-size: 16px; font-weight: 700; overflow-wrap: anywhere; }
        .history-time { font-size: 13px; color: var(--muted); margin-top: 4px; }
        .history-side { text-align: right; flex-shrink: 0; }
        .history-xp { background: color-mix(in srgb, var(--primary) 22%, transparent); color: var(--primary); padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: 700; }
        .history-toolbar { display:flex; gap:8px; align-items:center; justify-content:space-between; flex-wrap:wrap; margin-bottom:12px; }
        .history-toolbar .form-control { max-width: 320px; }
        .history-pager { display:flex; gap:8px; align-items:center; justify-content:flex-end; margin-top:10px; }
        .history-pager .muted { font-size:12px; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: middle; }
        th { color: var(--muted); font-size: 14px;}
        .ranking-table td { white-space: nowrap; }
        .rank-user { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .rank-level-cell { min-width: 84px; }
        .rank-level-badge {
            display: inline-block;
            background: var(--primary);
            color: #0b1220;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            line-height: 1;
            white-space: nowrap;
        }
        
        .avatar-img { width: 100%; height: 100%; object-fit: cover; }
        .ingredient-tag { padding: 6px 12px; border-radius: 16px; cursor: pointer; font-size: 13px; font-weight: bold; transition: 0.2s; }
        .glass-tag { padding: 8px 12px; border-radius: 12px; cursor: pointer; font-size: 13px; font-weight: bold; transition: 0.2s; border: 1px solid var(--border); background: var(--surface-2); }
        .serve-mode-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:12px; }
        .serve-mode-box { background: var(--surface-2); border:1px solid var(--border); border-radius:10px; padding:10px; }
        .serve-mode-box h4 { margin:0 0 10px; color:var(--primary); text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
        .serve-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
        .serve-row input { width:70px; }

        .modal-backdrop { position: fixed; inset: 0; background: rgba(1, 6, 15, 0.75); display: none; align-items: center; justify-content: center; z-index: 120; padding: 16px; }
        .modal-backdrop.open { display: flex; }
        .modal-card { width: 100%; max-width: 760px; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 18px; box-shadow: 0 20px 40px rgba(0,0,0,0.45); }
        .glass-picker, .mode-picker { display:grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 10px 0 14px; }
        .pick-item { border: 1px solid var(--border); background: var(--bg); border-radius: 10px; padding: 10px; cursor: pointer; text-align:center; }
        .pick-item.active { border-color: var(--primary); background: rgba(16, 185, 129, 0.12); }
        .pick-item .ico { font-size: 22px; display:block; margin-bottom: 6px; }
        .glass-list { display:flex; flex-direction:column; gap:10px; }
        .glass-card { display:flex; justify-content:space-between; gap:12px; padding:12px; background:var(--bg); border-radius:8px; border:1px solid var(--border); }
        .glass-meta { font-size:12px; color:var(--muted); margin-top:4px; line-height:1.45; }
        .serve-breakdown-row { display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:10px; background: var(--surface-2); border:1px solid var(--border); }
        .serve-breakdown-bar { width:10px; height:10px; border-radius:50%; background:var(--primary); flex:0 0 auto; }
        .serve-breakdown-text { flex:1; min-width:0; }
        .serve-breakdown-text strong { display:block; color:var(--text); }
        .serve-breakdown-text span { display:block; font-size:12px; color:var(--muted); }
                .table-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
                #sb-info { overflow-wrap: anywhere; }

                @media (max-width: 768px) {
                        .sidebar { width: min(88vw, 320px); }
                        .sidebar-header { padding: 20px 14px; }
                        .main-content { padding: 12px; }
                        .card { padding: 16px; margin-bottom: 16px; }
                        .grid-2, .grid-3 { grid-template-columns: 1fr; gap: 12px; }
                        .camera-feed { height: 220px; }
                        .recipe-card > div:last-child { flex-wrap: wrap; gap: 8px; }
                        .recipe-card > div:last-child .btn { width: 100%; }
                        .history-item { flex-direction: column; align-items: stretch; }
                        .history-side { width: 100%; display: flex; justify-content: space-between; align-items: center; text-align: left; }
                        .table-wrap table { min-width: 760px; }
                        #view-ranking .table-wrap table { min-width: 680px; }
                        .rank-user { max-width: 120px; }
                        .rank-level-cell { min-width: 72px; }
                        .rank-level-badge { padding: 3px 7px; font-size: 11px; }
                        #create-user-form { flex-direction: column; align-items: stretch !important; }
                        #create-user-form .form-group,
                        #create-user-form .form-group[style] { width: 100% !important; }
                        #create-user-form button { width: 100%; }
                        #add-recipe-form > div[style*="display:flex"] { flex-direction: column; }
                        #add-recipe-form > div[style*="display:flex"] > * { width: 100% !important; }
                        #profile-form .form-control { width: 100%; }
                        #view-dashboard .card > div[style*="justify-content:space-between"] { flex-wrap: wrap; gap: 10px; }
                        #view-dashboard .card > div[style*="justify-content:space-between"] > div[style*="text-align:right"] { width: 100%; }
                        .modal-card { max-height: calc(100vh - 32px); overflow-y: auto; }
                }
      </style>
    </head>
    <body>
      <div class="app-container">
        
        <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>

        <!-- Sidebar Navigation -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h1>CUBATRON</h1>
                <div style="display:flex; flex-direction:column; align-items:center; gap:12px;">
                    <div id="sb-avatar" style="width:100px; height:100px; border-radius:50%; background:var(--bg); display:flex; align-items:center; justify-content:center; overflow:hidden; font-size:40px; border: 3px solid var(--primary);">👤</div>
                    <div>
                        <div id="sb-name" style="font-weight:bold; font-size:20px; margin-bottom:4px;">Cargando...</div>
                        <div id="sb-info" style="font-size:13px; color:var(--muted); margin-bottom:4px; min-height:18px;">&nbsp;</div>
                        <div id="sb-level" style="font-size:16px; color:var(--primary); font-weight:800;">LVL -</div>
                    </div>
                </div>
                <div style="margin-top:20px; text-align:left;">
                    <div style="font-size:13px; color:var(--muted); display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span>PROGRESO XP</span><span id="sb-xp">0 / 100</span>
                    </div>
                    <div style="height:10px; background:var(--bg); border-radius:5px; overflow:hidden;">
                        <div id="sb-xp-bar" style="height:100%; background:var(--primary); width:0%; transition: width 0.5s ease;"></div>
                    </div>
                </div>
            </div>
            
            <nav class="nav-menu">
                <a class="active" onclick="switchView('dashboard')">Inicio</a>
                <a onclick="switchView('machine')">Sistema</a>
                <a onclick="switchView('ranking')">Ranking</a>
                <a onclick="switchView('profile')">Mi Perfil</a>
                <a id="nav-admin" style="display:none;" onclick="switchView('admin')">ADMIN</a>
                <div style="flex-grow:1;"></div>
                <a onclick="logout()" style="color:var(--danger);">Salir</a>
            </nav>
        </aside>

        <!-- Main Content Area -->
        <div class="main-content">
            
            <div class="mobile-topbar">
                <button class="hamburger" onclick="toggleSidebar()">☰</button>
                <h1 style="margin:0; font-size:20px; color:var(--primary);">CUBATRON</h1>
                <div style="width:24px;"></div>
            </div>

            <!-- VIEW: INICIO (Tres filas apiladas) -->
            <div id="view-dashboard" class="view-section active">
                
                <!-- 1. Estado de la máquina (Ancho completo) -->
                <div class="card" style="margin-bottom: 16px; padding:16px 18px;">
                    <h2>Estado de la Máquina</h2>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div id="machine-status" class="status-indicator compact status-OFFLINE">
                            <div class="status-dot"></div><span id="status-text">OFFLINE</span>
                        </div>
                        <div class="status-24h-box">
                            <p class="status-24h-label">Consumiciones en 24h</p>
                            <strong id="status-drinks" class="status-24h-value">0</strong>
                        </div>
                    </div>
                </div>

                <!-- 2. Recetas Disponibles (Ancho completo, Grid-3 dentro) -->
                <div class="card" style="margin-bottom: 24px;">
                    <h2>Recetas Disponibles</h2>
                    <div id="recipes-list" class="grid-3"><p class="muted">Cargando...</p></div>
                </div>

                <!-- 3. Tus Últimas Consumiciones (Ancho completo) -->
                <div class="card" style="margin-bottom: 24px;">
                    <h2>Últimas Consumiciones Realizadas</h2>
                    <div class="history-toolbar">
                        <input id="global-history-filter" type="text" class="form-control" placeholder="Filtrar por bebida o usuario">
                        <button class="btn btn-small btn-secondary" onclick="applyGlobalHistoryFilter()">Filtrar</button>
                    </div>
                    <div id="global-history-list" style="display:flex; flex-direction:column; gap:12px;">
                        <p class="muted">Aún no has preparado nada.</p>
                    </div>
                    <div class="history-pager">
                        <button class="btn btn-small btn-secondary" onclick="changeGlobalHistoryPage(-1)">Anterior</button>
                        <span id="global-history-page" class="muted">Página 1 / 1</span>
                        <button class="btn btn-small btn-secondary" onclick="changeGlobalHistoryPage(1)">Siguiente</button>
                    </div>
                </div>

            </div>

            <!-- VIEW: SISTEMA -->
            <div id="view-machine" class="view-section">
                <div class="grid-2">
                    <div class="card">
                        <h2>Cámara en Vivo</h2>
                        <div class="camera-feed">
                            <span style="font-family:monospace; opacity:0.5;">[ CÁMARA NO CONECTADA ]</span>
                        </div>
                        <div style="margin-top: 16px; display:flex; gap:8px;">
                            <button class="btn btn-secondary" onclick="machineAction('prime')">Cebar Circuito</button>
                            <button class="btn btn-secondary" onclick="machineAction('clean')">Limpieza Auto</button>
                        </div>
                    </div>

                    <div class="card">
                        <h2>Estado de Depósitos</h2>
                        <div id="tanks-list" style="display:flex; flex-direction:column; gap:16px;"></div>
                        <button class="btn" style="margin-top:20px; width:100%;" onclick="saveTanks()">Guardar Depósitos</button>
                    </div>
                </div>
            </div>

            <!-- VIEW: ADMIN -->
            <div id="view-admin" class="view-section">
                
                <!-- CREACIÓN DE USUARIOS -->
                <div class="card" style="margin-bottom:24px;">
                    <h2>Crear Nuevo Usuario</h2>
                    <form id="create-user-form" onsubmit="createUser(event)" style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
                        <div class="form-group" style="margin:0; flex:1;">
                            <input type="text" id="cu-username" class="form-control" placeholder="Nombre de usuario" required>
                        </div>
                        <div class="form-group" style="margin:0; flex:1;">
                            <input type="text" id="cu-fullname" class="form-control" placeholder="Nombre completo" required>
                        </div>
                        <div class="form-group" style="margin:0; flex:1;">
                            <input type="password" id="cu-password" class="form-control" placeholder="Contraseña" required>
                        </div>
                        <div class="form-group" style="margin:0; width:150px;">
                            <select id="cu-role" class="form-control">
                                <option value="user">Usuario</option>
                                <option value="admin">Administrador</option>
                            </select>
                        </div>
                        <button type="submit" class="btn" style="margin:0;">Crear Usuario</button>
                    </form>
                </div>

                <div class="card" style="margin-bottom:24px;">
                    <h2>Gestión de Recetas</h2>
                    <p class="muted" style="font-size:14px;">Configura ingredientes, tipos de vaso y perfiles LOW/MEDIUM/HIGH/EXTREME por receta.</p>
                    <div id="admin-recipes-list" style="margin-bottom:16px;"></div>
                    
                    <form id="add-recipe-form" onsubmit="addRecipe(event)" style="display:flex; flex-direction:column; gap:12px; background:var(--bg); padding:16px; border-radius:8px; border:1px solid var(--border);">
                        <input type="hidden" id="nr-id" value="">
                        <div style="display:flex; gap:8px; flex-wrap:wrap;">
                            <input type="text" id="nr-name" class="form-control" placeholder="Nombre (Ej: Ron Cola)" required style="flex:1; min-width:150px;">
                            <input type="number" id="nr-xp" class="form-control" placeholder="XP" required style="width:80px;" value="150">
                        </div>
                        <input type="text" id="nr-desc" class="form-control" placeholder="Descripción breve" required>
                        
                        <div>
                            <label style="font-size:13px; color:var(--muted); margin-bottom:8px; display:block;">Requerimientos (Clic para seleccionar):</label>
                            <div id="nr-ing-selector" style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px;">
                                <!-- Los botones de los líquidos se generarán aquí -->
                            </div>
                            <input type="hidden" id="nr-ing-hidden" value="">
                        </div>

                        <div>
                            <label style="font-size:13px; color:var(--muted); margin-bottom:8px; display:block;">Tipos de vaso disponibles:</label>
                            <div id="nr-glass-selector" style="display:flex; gap:8px; flex-wrap:wrap;"></div>
                        </div>

                        <div>
                            <label style="font-size:13px; color:var(--muted); margin-bottom:8px; display:block;">Distribución por modo (%)</label>
                            <div id="nr-serving-modes" class="serve-mode-grid"></div>
                        </div>

                        <div style="display:flex; gap:8px;">
                            <button type="submit" id="nr-submit" class="btn" style="align-self:flex-start;">Añadir Receta</button>
                            <button type="button" class="btn btn-secondary" onclick="resetRecipeForm()">Cancelar edición</button>
                        </div>
                    </form>
                </div>

                <div class="card" style="margin-bottom:24px;">
                    <h2>Gestión de Vasos</h2>
                    <p class="muted" style="font-size:14px;">Crea, edita o elimina vasos con su nombre, icono y capacidad fija en mL.</p>
                    <div id="admin-glasses-list" style="margin-bottom:16px;"></div>

                    <form id="glass-form" onsubmit="saveGlass(event)" style="display:flex; flex-direction:column; gap:12px; background:var(--bg); padding:16px; border-radius:8px; border:1px solid var(--border);">
                        <input type="hidden" id="gl-id" value="">
                        <input type="hidden" id="gl-key" value="">
                        <div style="display:flex; gap:8px; flex-wrap:wrap;">
                            <input type="text" id="gl-name" class="form-control" placeholder="Nombre (ej: Highball)" required style="flex:1; min-width:180px;" oninput="syncGlassKey()">
                        </div>
                        <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                            <input type="text" id="gl-icon" class="form-control" placeholder="Icono" value="🥤" required style="width:120px;">
                            <input type="number" id="gl-capacity" class="form-control" placeholder="Capacidad mL" min="30" max="2000" required style="width:180px;" value="300">
                            <label style="display:flex; align-items:center; gap:8px; color:var(--muted); font-size:13px;">
                                <input type="checkbox" id="gl-enabled" checked>
                                Habilitado
                            </label>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button type="submit" id="gl-submit" class="btn">Añadir vaso</button>
                            <button type="button" class="btn btn-secondary" onclick="resetGlassForm()">Cancelar edición</button>
                        </div>
                    </form>
                </div>
                
                <div class="grid-2">
                    <div class="card">
                        <h2>Líquidos del Sistema</h2>
                        <p class="muted" style="font-size:14px;">Gestiona qué líquidos se pueden usar en los depósitos.</p>
                        <div id="admin-liquids-list" style="margin-bottom:16px;"></div>
                        <div style="display:flex; gap:8px;">
                            <input type="text" id="new-liq-name" class="form-control" placeholder="Nombre (Ej: Fanta)">
                            <select id="new-liq-type" class="form-control" style="width:140px;">
                                <option value="mixer">Mezcla</option>
                                <option value="alcohol">Alcohol</option>
                            </select>
                            <button class="btn" onclick="addLiquid()">Añadir</button>
                        </div>
                    </div>

                    <div class="card">
                        <h2>Tiempos de Actualización</h2>
                        <form id="settings-form" onsubmit="saveSettings(event)">
                            <div class="form-group"><label>Refresco Estado (ms)</label><input type="number" id="set-status" class="form-control"></div>
                            <div class="form-group"><label>Refresco Depósitos (ms)</label><input type="number" id="set-tanks" class="form-control"></div>
                            <button type="submit" class="btn">Aplicar Tiempos</button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- VIEW: RANKING -->
            <div id="view-ranking" class="view-section">
                <div class="card">
                    <h2>Ranking Global</h2>
                    <div class="table-wrap">
                        <table class="ranking-table">
                            <thead><tr><th>FOTO</th><th>POS</th><th>USUARIO</th><th>NIVEL</th><th>XP</th><th>CONSUMICIONES</th><th>BEBIDA MAS CONSUMIDA</th></tr></thead>
                            <tbody id="ranking-list"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- VIEW: MI PERFIL -->
            <div id="view-profile" class="view-section">
                <div class="grid-2">
                    <div class="card">
                        <h2>Actualizar Información</h2>
                        <form id="profile-form" onsubmit="updateProfile(event)">
                            <div class="form-group" style="text-align: center;">
                                <div id="edit-avatar-preview" style="width:120px; height:120px; border-radius:50%; background:var(--bg); margin:0 auto 16px; display:flex; align-items:center; justify-content:center; overflow:hidden; font-size:40px; border:2px solid var(--primary);">👤</div>
                                <input type="file" id="edit-avatar" accept="image/*" class="form-control" style="background:var(--surface-2);">
                            </div>
                            <div class="form-group"><label>Nombre a mostrar</label><input type="text" id="edit-fullname" class="form-control"></div>
                            <div class="form-group">
                                <label>Bebida Favorita</label>
                                <select id="edit-mix" class="form-control">
                                    <option value="">-- Sin favorita --</option>
                                </select>
                            </div>
                            <div class="form-group"><label>Info</label><input type="text" id="edit-info" class="form-control" maxlength="140" placeholder="Tu estado o info personal"></div>
                            <button type="submit" class="btn" style="width:100%;">Guardar Cambios</button>
                        </form>
                    </div>
                    
                    <div class="card" style="height: fit-content;">
                        <h2>Interfaz</h2>
                        <div class="form-group">
                            <label>Tema</label>
                            <select id="ui-theme" class="form-control">
                                <option value="dark">Oscuro</option>
                                <option value="light">Claro</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Acento</label>
                            <select id="ui-accent" class="form-control">
                                <option value="emerald">Verde</option>
                                <option value="blue">Azul</option>
                                <option value="orange">Naranja</option>
                                <option value="rose">Rosa</option>
                                <option value="slate">Pizarra</option>
                            </select>
                        </div>
                        <p style="font-size:12px; color:var(--muted); margin:0;">Se guardan por usuario y se aplican al iniciar sesión.</p>
                    </div>

                    <div class="card" style="height: fit-content;">
                        <h2>Seguridad</h2>
                        <form id="password-form" onsubmit="updatePassword(event)">
                            <div class="form-group"><label>Nueva Contraseña</label><input type="password" id="edit-password" class="form-control" required></div>
                            <button type="submit" class="btn btn-secondary" style="width:100%;">Actualizar Contraseña</button>
                        </form>
                    </div>
                </div>
                <div class="card" style="margin-top: 8px;">
                    <h2>Tus Últimas Consumiciones</h2>
                    <div class="history-toolbar">
                        <input id="my-history-filter" type="text" class="form-control" placeholder="Filtrar por bebida">
                        <button class="btn btn-small btn-secondary" onclick="applyMyHistoryFilter()">Filtrar</button>
                    </div>
                    <div id="my-history-list" style="display:flex; flex-direction:column; gap:12px;">
                        <p class="muted">Aún no has preparado nada.</p>
                    </div>
                    <div class="history-pager">
                        <button class="btn btn-small btn-secondary" onclick="changeMyHistoryPage(-1)">Anterior</button>
                        <span id="my-history-page" class="muted">Página 1 / 1</span>
                        <button class="btn btn-small btn-secondary" onclick="changeMyHistoryPage(1)">Siguiente</button>
                    </div>
                </div>
            </div>

        </div>
      </div>

      <div id="serve-modal" class="modal-backdrop" onclick="closeServeModal(event)">
        <div class="modal-card" onclick="event.stopPropagation()">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <h3 id="serve-title" style="margin:0; color:var(--primary);">Configurar servicio</h3>
                <button class="btn btn-secondary btn-small" onclick="closeServeModal()">Cerrar</button>
            </div>
            <p id="serve-desc" style="margin:8px 0 10px; color:var(--muted);">Selecciona vaso y modo.</p>

            <label style="font-size:13px; color:var(--muted);">Tipo de vaso</label>
            <div id="serve-glass-picker" class="glass-picker"></div>

            <label style="font-size:13px; color:var(--muted);">Modo de servido</label>
            <div id="serve-mode-picker" class="mode-picker"></div>
            <p id="serve-ml-estimate" style="margin:8px 0 0; font-size:12px; color:var(--muted);"></p>
            <p id="serve-xp-estimate" style="margin:4px 0 0; font-size:12px; color:var(--primary); font-weight:700;"></p>
            <div id="serve-breakdown" style="margin-top:10px; display:flex; flex-direction:column; gap:6px;"></div>

            <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:8px;">
                <button class="btn btn-secondary" onclick="closeServeModal()">Cancelar</button>
                <button class="btn" onclick="confirmServeDrink()">Preparar</button>
            </div>
        </div>
      </div>

      <script>
        const tokenKey = "cubatron_token";
        let currentUser = null; let currentTanks = [];
        let systemSettings = { poll_status: 3000, poll_tanks: 10000, poll_history: 30000, liquids: [] };
        const DEFAULT_GLASS_CATALOG = {
            highball: { label: "Highball", icon: "🥤" },
            rocks: { label: "Rocks", icon: "🥃" },
            coupe: { label: "Coupe", icon: "🍸" },
            hurricane: { label: "Hurricane", icon: "🍹" },
            shot: { label: "Shot", icon: "🧪" }
        };
        const MODE_XP_MULTIPLIER = { low: 0.9, medium: 1.0, high: 1.2, extreme: 1.4 };
        const SERVE_MODES = ["low", "medium", "high", "extreme"];
        const ACCENT_PALETTE = {
            emerald: { primary: "#10b981", hover: "#059669" },
            blue: { primary: "#3b82f6", hover: "#2563eb" },
            orange: { primary: "#f97316", hover: "#ea580c" },
            rose: { primary: "#f43f5e", hover: "#e11d48" },
            slate: { primary: "#64748b", hover: "#475569" },
        };

        function applyThemePreferences(themeMode = 'dark', accentColor = 'emerald') {
            const root = document.documentElement;
            const accent = ACCENT_PALETTE[accentColor] || ACCENT_PALETTE.emerald;

            if(themeMode === 'light') {
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
            if(!isoValue) return '';
            const raw = String(isoValue).trim();
            const hasTz = /(?:Z|[+-]\\d{2}:?\\d{2})$/i.test(raw);
            const normalized = hasTz ? raw : `${raw}Z`;
            const date = new Date(normalized);
            if(Number.isNaN(date.getTime())) return String(isoValue);

            const diffMs = date.getTime() - Date.now();
            const absMs = Math.abs(diffMs);
            const minute = 60 * 1000;
            const hour = 60 * minute;
            const day = 24 * hour;
            const month = 30 * day;
            const year = 365 * day;

            let value = 0;
            let unit = 'minute';

            if(absMs < minute) {
                return 'hace unos segundos';
            } else if(absMs < hour) {
                value = Math.round(diffMs / minute);
                unit = 'minute';
            } else if(absMs < day) {
                value = Math.round(diffMs / hour);
                unit = 'hour';
            } else if(absMs < month) {
                value = Math.round(diffMs / day);
                unit = 'day';
            } else if(absMs < year) {
                value = Math.round(diffMs / month);
                unit = 'month';
            } else {
                value = Math.round(diffMs / year);
                unit = 'year';
            }

            return new Intl.RelativeTimeFormat('es', { numeric: 'auto' }).format(value, unit);
        }

        let selectedIngredients = [];
        let selectedGlasses = ["highball"];
        let recipesCache = [];
        let adminRecipesCache = [];
        let activeGlassesCache = [];
        let adminGlassesCache = [];
        let tankSignature = "";

        let activeServeRecipe = null;
        let activeServeGlass = "highball";
        let activeServeMode = "medium";
        const globalHistoryState = { page: 1, pageSize: 8, q: '' };
        const myHistoryState = { page: 1, pageSize: 8, q: '' };

        function normalizeModeMap(rawModes, selected) {
            const safe = rawModes && typeof rawModes === 'object' ? rawModes : {};
            const out = {};
            SERVE_MODES.forEach(mode => {
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
            const source = activeGlassesCache.length > 0 ? activeGlassesCache : adminGlassesCache;
            const catalog = {};
            source.forEach(glass => {
                catalog[glass.key] = glass;
            });
            if (Object.keys(catalog).length === 0) {
                return DEFAULT_GLASS_CATALOG;
            }
            return catalog;
        }

        function getGlassInfo(glassKey) {
            const catalog = getGlassCatalog();
            const glass = catalog[glassKey];
            if (glass) return glass;
            return DEFAULT_GLASS_CATALOG[glassKey] || { key: glassKey, name: glassKey, icon: '🥤', capacity_ml: 300 };
        }

        function getRecipeGlassOptions(recipe) {
            const availableKeys = new Set((activeGlassesCache.length > 0 ? activeGlassesCache : adminGlassesCache).filter(g => g.enabled !== false).map(g => g.key));
            const fromRecipe = Array.isArray(recipe?.glass_options) ? recipe.glass_options : [];
            const filtered = fromRecipe.filter(key => availableKeys.has(key));
            if (filtered.length > 0) return filtered;
            const fallback = Array.from(availableKeys);
            return fallback.length > 0 ? fallback : Object.keys(DEFAULT_GLASS_CATALOG);
        }

        function computeServeXp(baseXp, capacityMl, modeKey) {
            const glassMult = Math.max(0.6, Math.min(2.2, Number(capacityMl || 300) / 300));
            const modeMult = MODE_XP_MULTIPLIER[modeKey] || 1.0;
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

        function renderGlassSelector() {
            const container = document.getElementById('nr-glass-selector');
            if(!container) return;
            const keys = getRecipeGlassOptions({ glass_options: activeGlassesCache.map(g => g.key) });
            if(keys.length === 0) {
                container.innerHTML = '<p style="margin:0; font-size:12px; color:var(--muted);">No hay vasos habilitados.</p>';
                return;
            }
            container.innerHTML = keys.map(k => {
                const g = getGlassInfo(k);
                const selected = selectedGlasses.includes(k);
                return `<div class="glass-tag" onclick="toggleGlass('${k}')" style="border-color:${selected ? 'var(--primary)' : 'var(--border)'}; background:${selected ? 'rgba(16, 185, 129, 0.18)' : 'var(--surface-2)'};">${g.icon || '🥤'} ${g.name || g.label || k} ${selected ? '✓' : '+'}</div>`;
            }).join('');
        }

        function toggleGlass(glassKey) {
            if(selectedGlasses.includes(glassKey)) {
                if(selectedGlasses.length === 1) return;
                selectedGlasses = selectedGlasses.filter(g => g !== glassKey);
            } else {
                selectedGlasses.push(glassKey);
            }
            renderGlassSelector();
        }

        function renderServingModesEditor(existing = null) {
            const container = document.getElementById('nr-serving-modes');
            if(!container) return;

            const selected = selectedIngredients.slice();
            const sourceModes = existing || collectServingModes();
            const safeModes = normalizeModeMap(sourceModes, selected);

            container.innerHTML = SERVE_MODES.map(mode => {
                const rows = selected.map(liq => {
                    const value = safeModes[mode][liq] ?? 0;
                    return `<div class="serve-row"><span style="flex:1; font-size:12px; color:var(--muted);">${liq}</span><input class="form-control" type="number" min="0" max="100" step="1" data-mode="${mode}" data-liq="${liq}" value="${value}"><span>%</span></div>`;
                }).join('') || '<p style="margin:0; font-size:12px; color:var(--muted);">Selecciona ingredientes para definir porcentajes.</p>';

                return `<div class="serve-mode-box"><h4>${mode}</h4>${rows}</div>`;
            }).join('');
        }

        function collectServingModes() {
            const modes = {};
            SERVE_MODES.forEach(mode => modes[mode] = {});
            document.querySelectorAll('#nr-serving-modes input[data-mode][data-liq]').forEach(el => {
                const mode = el.dataset.mode;
                const liq = el.dataset.liq;
                const value = Number(el.value);
                modes[mode][liq] = Number.isFinite(value) ? value : 0;
            });
            return modes;
        }

        function getRecipeById(id) {
            return recipesCache.find(r => Number(r.id) === Number(id));
        }

        function computeServeMl(glassKey, modeKey) {
            return Number(getGlassInfo(glassKey).capacity_ml || 300);
        }

        function updateServeEstimate() {
            const estimateEl = document.getElementById('serve-ml-estimate');
            const xpEl = document.getElementById('serve-xp-estimate');
            const breakdownEl = document.getElementById('serve-breakdown');
            if(!estimateEl || !xpEl || !breakdownEl || !activeServeRecipe) return;

            const glass = getGlassInfo(activeServeGlass);
            const totalMl = computeServeMl(activeServeGlass, activeServeMode);
            const profile = activeServeRecipe.serving_modes?.[activeServeMode] || {};
            const breakdown = buildLiquidBreakdown(profile, totalMl);
            const xpValue = computeServeXp(activeServeRecipe.xp_reward, totalMl, activeServeMode);

            estimateEl.innerText = `Vaso: ${glass.name || glass.label || activeServeGlass} · Capacidad fija: ${totalMl} ml`;
            xpEl.innerText = `XP estimado: ${xpValue}`;
            breakdownEl.innerHTML = breakdown.length > 0
                ? breakdown.map(item => {
                    const pctText = `${item.pct}%`;
                    return `<div class="serve-breakdown-row"><div class="serve-breakdown-bar"></div><div class="serve-breakdown-text"><strong>${escapeHtml(item.liquid)}: ${item.ml} ml</strong><span>${pctText} del vaso</span></div></div>`;
                }).join('')
                : '<p style="margin:0; font-size:12px; color:var(--muted);">No hay perfil de servido para este modo.</p>';
        }

        function renderServePickers() {
            if(!activeServeRecipe) return;
            const recipe = activeServeRecipe;
            const availableGlasses = getRecipeGlassOptions(recipe);
            const modeKeys = Object.keys(recipe.serving_modes || {});
            const toRenderModes = modeKeys.length > 0 ? modeKeys : SERVE_MODES;

            const glassPicker = document.getElementById('serve-glass-picker');
            if(!availableGlasses.length) {
                glassPicker.innerHTML = '<p style="margin:0; font-size:12px; color:var(--muted);">No hay vasos disponibles.</p>';
                document.getElementById('serve-mode-picker').innerHTML = '';
                updateServeEstimate();
                return;
            }
            glassPicker.innerHTML = availableGlasses.map(g => {
                const info = getGlassInfo(g);
                const baseMl = Number(info.capacity_ml || 300);
                return `<div class="pick-item ${g === activeServeGlass ? 'active' : ''}" onclick="pickServeGlass('${g}')"><span class="ico">${info.icon || '🥤'}</span><strong>${info.name || info.label || g}</strong><div style="font-size:11px; color:var(--muted); margin-top:4px;">${baseMl} mL</div></div>`;
            }).join('');

            const modePicker = document.getElementById('serve-mode-picker');
            modePicker.innerHTML = toRenderModes.map(m => {
                const profile = recipe.serving_modes?.[m] || {};
                const profileText = Object.entries(profile).map(([liq, pct]) => `${liq} ${pct}%`).join(' · ');
                const totalMl = computeServeMl(activeServeGlass, m);
                const xpValue = computeServeXp(recipe.xp_reward, totalMl, m);
                return `<div class="pick-item ${m === activeServeMode ? 'active' : ''}" onclick="pickServeMode('${m}')"><strong style="text-transform:uppercase;">${m}</strong><div style="font-size:11px; color:var(--muted); margin-top:4px;">${totalMl} ml · ${xpValue} XP</div><div style="font-size:11px; color:var(--muted); margin-top:4px;">${profileText || 'Sin perfil'}</div></div>`;
            }).join('');

            updateServeEstimate();
        }

        function resetRecipeForm() {
            const form = document.getElementById('add-recipe-form');
            form.reset();
            document.getElementById('nr-id').value = '';
            document.getElementById('nr-submit').innerText = 'Añadir Receta';
            selectedIngredients = [];
            selectedGlasses = getRecipeGlassOptions({ glass_options: [activeGlassesCache[0]?.key || 'highball'] }).slice(0, 1);
            if(selectedGlasses.length === 0) selectedGlasses = ['highball'];
            renderIngredientSelector();
            renderGlassSelector();
            renderServingModesEditor();
        }
        
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
            document.getElementById('overlay').classList.toggle('open');
        }

        function switchView(viewId) {
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-menu a').forEach(el => el.classList.remove('active'));
            document.getElementById('view-' + viewId).classList.add('active');
            event.currentTarget.classList.add('active');
            if(window.innerWidth <= 768) toggleSidebar();
            
            if(viewId === 'ranking') loadRanking();
            if(viewId === 'admin') loadSettings();
            if(viewId === 'dashboard') loadGlobalHistory();
            if(viewId === 'profile') loadMyHistory();
        }

        function getToken() { return sessionStorage.getItem(tokenKey); }
        function logout() { sessionStorage.removeItem(tokenKey); window.location.href = "/"; }
        function authHeaders() { return { "Authorization": "Bearer " + getToken() }; }

        async function apiGet(url) {
            const res = await fetch(url, { headers: authHeaders() });
            if (res.status === 401) {
                sessionStorage.removeItem(tokenKey);
                window.location.href = "/";
                throw new Error("unauthorized");
            }
            if (!res.ok) throw new Error(res.status);
            return await res.json();
        }
        async function apiPost(url, body) {
            const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify(body) });
            if (res.status === 401) {
                sessionStorage.removeItem(tokenKey);
                window.location.href = "/";
                throw new Error("unauthorized");
            }
            if (!res.ok) throw new Error(res.status);
            return await res.json();
        }

        async function loadFavoriteMixOptions(selectedValue = '') {
            const selectEl = document.getElementById('edit-mix');
            if(!selectEl) return;
            try {
                const recipes = await apiGet('/api/drinks/recipes');
                const options = ['<option value="">-- Sin favorita --</option>'];
                (recipes || []).forEach(r => {
                    const name = escapeHtml(r.name || '');
                    if(!name) return;
                    options.push(`<option value="${name}">${name}</option>`);
                });
                selectEl.innerHTML = options.join('');

                if(selectedValue) {
                    const available = Array.from(selectEl.options).some(o => o.value === selectedValue);
                    selectEl.value = available ? selectedValue : '';
                } else {
                    selectEl.value = '';
                }
            } catch (_) {
                selectEl.innerHTML = '<option value="">-- Sin favorita --</option>';
            }
        }

        // Profile & History
        async function loadProfile() {
            currentUser = await apiGet("/api/users/me");
            document.getElementById('sb-name').innerText = currentUser.full_name || currentUser.username;
            document.getElementById('sb-info').innerText = (currentUser.info || '').trim() || '\u00a0';
            document.getElementById('sb-level').innerText = 'LVL ' + currentUser.level;
            
            let xpCurrent = currentUser.xp % 100;
            document.getElementById('sb-xp').innerText = `${xpCurrent} / 100`;
            document.getElementById('sb-xp-bar').style.width = `${xpCurrent}%`;
            
            if(currentUser.avatar_url) {
                const img = `<img src="${currentUser.avatar_url}" class="avatar-img">`;
                document.getElementById('sb-avatar').innerHTML = img;
                document.getElementById('edit-avatar-preview').innerHTML = img;
            }

            document.getElementById('edit-fullname').value = currentUser.full_name || '';
            document.getElementById('edit-info').value = currentUser.info || '';
            await loadFavoriteMixOptions(currentUser.favorite_mix || '');
            document.getElementById('ui-theme').value = currentUser.theme_mode || 'dark';
            document.getElementById('ui-accent').value = currentUser.accent_color || 'emerald';
            applyThemePreferences(currentUser.theme_mode || 'dark', currentUser.accent_color || 'emerald');
            if(currentUser.role === 'admin') document.getElementById('nav-admin').style.display = 'block';
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
            if(fileInput.files.length > 0) formData.append('avatar', fileInput.files[0]);
            
            await fetch("/api/users/me/update", { method: "POST", headers: { "Authorization": "Bearer " + getToken() }, body: formData });
            alert("Perfil actualizado");
            loadProfile();
        }

        async function updatePassword(ev) {
            ev.preventDefault();
            const pwd = document.getElementById('edit-password').value;
            try {
                await apiPost("/api/users/me/password", { new_password: pwd });
                alert("Contraseña actualizada con éxito");
                ev.target.reset();
            } catch(e) { alert("Error actualizando contraseña"); }
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
                        <span style="font-size:12px; color:var(--muted); display:block; margin-bottom:4px;">Completado</span>
                        <span class="history-xp">+${Number(h.xp || 0)} XP</span>
                    </div>
                </div>
            `).join('');
        }

        function updateHistoryPager(labelId, state, payload) {
            const page = Number(payload?.page || state.page || 1);
            const totalPages = Number(payload?.total_pages || 0);
            const safeTotalPages = totalPages > 0 ? totalPages : 1;
            const label = document.getElementById(labelId);
            if(label) label.innerText = `Página ${page} / ${safeTotalPages}`;
            state.page = page;
        }

        async function loadGlobalHistory(resetPage = false) {
            try {
                if(resetPage) globalHistoryState.page = 1;
                const query = new URLSearchParams({
                    scope: 'all',
                    page: String(globalHistoryState.page),
                    page_size: String(globalHistoryState.pageSize),
                    q: globalHistoryState.q,
                });
                const payload = await apiGet(`/api/users/history?${query.toString()}`);
                const list = document.getElementById('global-history-list');
                const items = payload?.items || [];
                if(!list) return;
                if(items.length === 0) {
                    list.innerHTML = '<p class="muted">No hay consumiciones registradas.</p>';
                    updateHistoryPager('global-history-page', globalHistoryState, payload);
                    return;
                }
                list.innerHTML = renderHistoryCards(items, true);
                updateHistoryPager('global-history-page', globalHistoryState, payload);
            } catch(e) {
                console.error('Error cargando historial global', e);
            }
        }

        async function loadMyHistory(resetPage = false) {
            try {
                if(resetPage) myHistoryState.page = 1;
                const query = new URLSearchParams({
                    scope: 'me',
                    page: String(myHistoryState.page),
                    page_size: String(myHistoryState.pageSize),
                    q: myHistoryState.q,
                });
                const payload = await apiGet(`/api/users/history?${query.toString()}`);
                const list = document.getElementById('my-history-list');
                const items = payload?.items || [];
                if(!list) return;
                if(items.length === 0) {
                    list.innerHTML = '<p class="muted">Aún no has preparado nada.</p>';
                    updateHistoryPager('my-history-page', myHistoryState, payload);
                    return;
                }
                list.innerHTML = renderHistoryCards(items, false);
                updateHistoryPager('my-history-page', myHistoryState, payload);
            } catch(e) {
                console.error('Error cargando historial personal', e);
            }
        }

        function applyGlobalHistoryFilter() {
            globalHistoryState.q = (document.getElementById('global-history-filter')?.value || '').trim();
            loadGlobalHistory(true);
        }

        function changeGlobalHistoryPage(delta) {
            const nextPage = Math.max(1, Number(globalHistoryState.page) + Number(delta || 0));
            if(nextPage === globalHistoryState.page) return;
            globalHistoryState.page = nextPage;
            loadGlobalHistory();
        }

        function applyMyHistoryFilter() {
            myHistoryState.q = (document.getElementById('my-history-filter')?.value || '').trim();
            loadMyHistory(true);
        }

        function changeMyHistoryPage(delta) {
            const nextPage = Math.max(1, Number(myHistoryState.page) + Number(delta || 0));
            if(nextPage === myHistoryState.page) return;
            myHistoryState.page = nextPage;
            loadMyHistory();
        }

        // System & Tanks
        async function pollMachineStatus() {
            try {
                const data = await apiGet("/api/machine/status");
                document.getElementById("machine-status").className = `status-indicator compact status-${data.status}`;
                document.getElementById("status-text").innerText = data.status;
                
                if(data.drinks_24h !== undefined) {
                    document.getElementById("status-drinks").innerText = data.drinks_24h;
                }

                const incomingTanks = data.tanks || [];
                const newSignature = JSON.stringify(
                    incomingTanks.map(t => [t.id, t.name || '', t.current_level || 0, t.current_ml || 0])
                );
                const changed = newSignature !== tankSignature;

                if(!document.querySelector('select:focus') && !document.querySelector('input:focus')) {
                    currentTanks = incomingTanks;
                    renderTanks();
                }

                if(changed) {
                    tankSignature = newSignature;
                    await loadRecipes();
                }
            } catch(e) {}
        }

        function renderTanks() {
            const container = document.getElementById('tanks-list');
            if(container.innerHTML.includes('focus')) return;
            
            const liquids = systemSettings.liquids || [];
            
            container.innerHTML = currentTanks.map((t, i) => {
                let options = liquids.map(l => `<option value="${l.name}" ${t.name === l.name ? 'selected' : ''}>${l.name}</option>`).join('');
                
                return `
                <div class="tank-item">
                    <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                        <strong style="color:var(--primary);">Depósito ${t.id}</strong>
                        <button class="btn btn-small btn-secondary" onclick="machineAction('purge_tank_${t.id}')">Purgar</button>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 100px; gap:12px; align-items:center;">
                        <select class="form-control" id="tank-name-${i}">
                            <option value="">-- Vacío / Seleccionar --</option>
                            ${options}
                        </select>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <input type="number" class="form-control" id="tank-level-${i}" value="${t.current_level || 0}">
                            <span>%</span>
                        </div>
                    </div>
                </div>
                `;
            }).join("");
        }

        async function saveTanks() {
            const updates = currentTanks.map((t, i) => {
                const selectedName = document.getElementById(`tank-name-${i}`).value || "";
                const liquidInfo = (systemSettings.liquids || []).find(l => l.name === selectedName);
                const levelVal = parseInt(document.getElementById(`tank-level-${i}`).value) || 0;

                return {
                    id: t.id,
                    name: selectedName,
                    liquid_type: liquidInfo ? liquidInfo.type : 'mixer',
                    current_ml: levelVal
                };
            });
            
            try {
                await apiPost("/api/machine/tanks/update", updates);
                alert("Depósitos guardados con éxito");
                pollMachineStatus();
                loadRecipes();
            } catch (e) {
                alert("Error al guardar.");
            }
        }

        async function machineAction(action) {
            await apiPost(`/api/machine/action/${action}`, {});
            pollMachineStatus();
        }

        async function loadActiveGlasses() {
            try {
                const glasses = await apiGet('/api/drinks/glasses');
                activeGlassesCache = glasses || [];
            } catch(e) {
                activeGlassesCache = [];
            }

            if(selectedGlasses.length === 0 || !selectedGlasses.some(key => activeGlassesCache.some(g => g.key === key))) {
                selectedGlasses = activeGlassesCache.length > 0 ? [activeGlassesCache[0].key] : ['highball'];
            }

            renderGlassSelector();
            if(activeServeRecipe) renderServePickers();
        }

        async function loadAdminGlasses() {
            try {
                const glasses = await apiGet('/api/admin/glasses');
                adminGlassesCache = glasses || [];
            } catch(e) {
                adminGlassesCache = [];
            }
            renderAdminGlasses();
            renderGlassSelector();
            if(activeServeRecipe) renderServePickers();
        }

        // Recipes & Making Drinks
        async function loadRecipes() {
            try {
                const recipes = await apiGet("/api/drinks/recipes");
                recipesCache = recipes || [];
                const availableLiquids = currentTanks
                    .filter(t => t.current_level > 0 && t.name)
                    .map(t => t.name.toLowerCase().trim());
                
                document.getElementById("recipes-list").innerHTML = recipes.map(r => {
                    const reqString = r.ingredients || "";
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
                        return `<span style="color:var(--muted);">${escapeHtml(req)}</span>`;
                    }).join(', ');

                    return `
                    <div class="recipe-card ${canMake ? '' : 'disabled'}">
                        <div>
                            <h3 style="margin:0 0 8px; color:var(--primary);">${r.name}</h3>
                            <p class="muted" style="font-size:13px; margin:0 0 8px;">${r.description}</p>
                            <p style="font-size:12px; margin:0 0 16px;"><strong style="color:var(--muted);">Requiere:</strong> ${reqHtml || '<span style="color:var(--muted);">-</span>'}</p>
                        </div>
                        <div style="display:flex; justify-content:flex-end; align-items:center;">
                            <button class="btn" onclick="openServeModal(${r.id})">${canMake ? 'Preparar' : 'Faltan líquidos'}</button>
                        </div>
                    </div>
                    `;
                }).join("");
            } catch(e) {}
        }

        function openServeModal(id) {
            const recipe = getRecipeById(id);
            if(!recipe) return;

            activeServeRecipe = recipe;
            const availableGlasses = getRecipeGlassOptions(recipe);
            const modeKeys = Object.keys(recipe.serving_modes || {});

            activeServeGlass = availableGlasses[0] || activeGlassesCache[0]?.key || 'highball';
            activeServeMode = modeKeys.includes('medium') ? 'medium' : (modeKeys[0] || 'medium');

            document.getElementById('serve-title').innerText = `Preparar ${recipe.name}`;
            document.getElementById('serve-desc').innerText = recipe.description || 'Selecciona vaso y modo de servicio.';
            renderServePickers();

            document.getElementById('serve-modal').classList.add('open');
        }

        function pickServeGlass(glassKey) {
            activeServeGlass = glassKey;
            renderServePickers();
        }

        function pickServeMode(mode) {
            activeServeMode = mode;
            renderServePickers();
        }

        function closeServeModal(ev = null) {
            if(ev && ev.target && ev.target.id !== 'serve-modal') return;
            document.getElementById('serve-modal').classList.remove('open');
            activeServeRecipe = null;
        }

        async function confirmServeDrink() {
            if(!activeServeRecipe) return;
            await makeDrink(activeServeRecipe.id, activeServeMode, activeServeGlass);
            closeServeModal();
        }

        async function makeDrink(id, servingMode = 'medium', glassType = 'highball') {
            try {
                const res = await apiPost("/api/drinks/make", { recipe_id: id, serving_mode: servingMode, glass_type: glassType });
                const mlInfo = res.total_ml ? `\nVolumen: ${res.total_ml} ml` : '';
                alert(`¡Bebida en marcha! 🍹\nHas ganado ${res.xp_earned} XP${mlInfo}`);
                await loadProfile();
                await loadGlobalHistory();
                await loadMyHistory();
            } catch(e) { alert("Error al preparar la bebida."); }
        }

        // --- Admin Functions ---
        async function loadSettings() {
            document.getElementById('set-status').value = systemSettings.poll_status;
            document.getElementById('set-tanks').value = systemSettings.poll_tanks;
            renderAdminLiquids();
            renderIngredientSelector();
            renderGlassSelector();
            renderServingModesEditor();
            await loadAdminGlasses();
            loadAdminRecipes(); 
        }

        // CREAR USUARIO
        async function createUser(ev) {
            ev.preventDefault();
            const payload = {
                username: document.getElementById('cu-username').value,
                full_name: document.getElementById('cu-fullname').value || document.getElementById('cu-username').value,
                password: document.getElementById('cu-password').value,
                role: document.getElementById('cu-role').value
            };
            try {
                await apiPost("/api/admin/users/create", payload);
                alert("Usuario creado con éxito");
                ev.target.reset();
            } catch(e) {
                alert("Error al crear usuario.");
            }
        }

        function renderAdminLiquids() {
            const list = document.getElementById('admin-liquids-list');
            list.innerHTML = (systemSettings.liquids || []).map((l, i) => `
                <div style="display:flex; justify-content:space-between; padding:12px; background:var(--bg); border-radius:8px; margin-bottom:8px; border:1px solid var(--border);">
                    <span><strong style="color:var(--text);">${l.name}</strong> <span class="muted" style="margin-left:8px; font-size:12px;">(${l.type.toUpperCase()})</span></span>
                    <button class="btn btn-small btn-danger" onclick="deleteLiquid(${i})">X</button>
                </div>
            `).join('');
        }

        function renderAdminGlasses() {
            const list = document.getElementById('admin-glasses-list');
            if(!list) return;

            if(!adminGlassesCache || adminGlassesCache.length === 0) {
                list.innerHTML = '<p class="muted" style="margin:0;">No hay vasos configurados.</p>';
                return;
            }

            list.innerHTML = adminGlassesCache.map(glass => {
                const state = glass.enabled ? 'Habilitado' : 'Deshabilitado';
                return `
                    <div class="glass-card" style="align-items:flex-start;">
                        <div style="display:flex; gap:12px; align-items:flex-start; min-width:0;">
                            <div style="font-size:26px; line-height:1;">${escapeHtml(glass.icon || '🥤')}</div>
                            <div style="min-width:0;">
                                <strong style="color:var(--text);">${escapeHtml(glass.name || glass.key)}</strong>
                                <div class="glass-meta">Clave: ${escapeHtml(glass.key)} · ${Number(glass.capacity_ml || 0)} mL · ${state}</div>
                            </div>
                        </div>
                        <div style="display:flex; gap:8px; flex-shrink:0;">
                            <button class="btn btn-small btn-secondary" onclick="editGlass(${glass.id})">Editar</button>
                            <button class="btn btn-small btn-danger" onclick="deleteGlass(${glass.id})">X</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function syncGlassKey() {
            const keyInput = document.getElementById('gl-key');
            const nameInput = document.getElementById('gl-name');
            if(!keyInput || !nameInput) return;
            keyInput.value = slugifyGlassKey(nameInput.value);
        }

        function resetGlassForm() {
            const form = document.getElementById('glass-form');
            if(form) form.reset();
            document.getElementById('gl-id').value = '';
            document.getElementById('gl-key').value = '';
            document.getElementById('gl-name').value = '';
            document.getElementById('gl-icon').value = '🥤';
            document.getElementById('gl-capacity').value = 300;
            document.getElementById('gl-enabled').checked = true;
            document.getElementById('gl-submit').innerText = 'Añadir vaso';
        }

        function editGlass(id) {
            const glass = (adminGlassesCache || []).find(g => Number(g.id) === Number(id));
            if(!glass) return;

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
                if(glassId > 0) {
                    await apiPost(`/api/admin/glasses/${glassId}`, payload);
                } else {
                    await apiPost('/api/admin/glasses/create', { ...payload, key: document.getElementById('gl-key').value || slugifyGlassKey(payload.name) });
                }
                resetGlassForm();
                await loadAdminGlasses();
                await loadActiveGlasses();
                await loadRecipes();
            } catch(e) {
                alert('Error al guardar el vaso.');
            }
        }

        async function deleteGlass(id) {
            if(!confirm('¿Eliminar este vaso? Se retirará de las recetas donde aparezca.')) return;
            try {
                await fetch(`/api/admin/glasses/${id}`, { method: 'DELETE', headers: authHeaders() });
                if(Number(document.getElementById('gl-id').value || '0') === Number(id)) {
                    resetGlassForm();
                }
                await loadAdminGlasses();
                await loadActiveGlasses();
                await loadRecipes();
            } catch(e) {
                alert('Error al eliminar el vaso.');
            }
        }

        async function addLiquid() {
            const name = document.getElementById('new-liq-name').value;
            const type = document.getElementById('new-liq-type').value;
            if(!name) return;
            systemSettings.liquids.push({name, type});
            await apiPost("/api/admin/settings", systemSettings);
            document.getElementById('new-liq-name').value = '';
            renderAdminLiquids();
            renderIngredientSelector();
            renderServingModesEditor();
            renderTanks(); 
            loadRecipes();
        }

        async function deleteLiquid(index) {
            systemSettings.liquids.splice(index, 1);
            await apiPost("/api/admin/settings", systemSettings);
            selectedIngredients = selectedIngredients.filter(name => (systemSettings.liquids || []).some(l => l.name === name));
            renderAdminLiquids();
            renderIngredientSelector();
            renderServingModesEditor();
            renderTanks();
            loadRecipes();
        }

        async function saveSettings(ev) {
            ev.preventDefault();
            systemSettings.poll_status = parseInt(document.getElementById('set-status').value);
            systemSettings.poll_tanks = parseInt(document.getElementById('set-tanks').value);
            await apiPost("/api/admin/settings", systemSettings);
            alert("Configuración guardada");
        }

        function renderIngredientSelector() {
            const container = document.getElementById('nr-ing-selector');
            if(!container) return;
            
            const liquids = systemSettings.liquids || [];
            container.innerHTML = liquids.map(l => {
                const isSelected = selectedIngredients.includes(l.name);
                return `
                    <div class="ingredient-tag" onclick="toggleIngredient('${l.name}')" 
                         style="border:1px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}; 
                                background:${isSelected ? 'var(--primary)' : 'var(--surface-2)'}; 
                                color:${isSelected ? '#000' : 'var(--text)'};">
                        ${l.name} ${isSelected ? '✓' : '+'}
                    </div>
                `;
            }).join('');
            
            document.getElementById('nr-ing-hidden').value = selectedIngredients.join(', ');
        }

        function toggleIngredient(name) {
            if(selectedIngredients.includes(name)) {
                selectedIngredients = selectedIngredients.filter(n => n !== name);
            } else {
                selectedIngredients.push(name);
            }
            renderIngredientSelector();
            renderServingModesEditor();
        }

        async function addRecipe(ev) {
            ev.preventDefault();
            const reqs = document.getElementById('nr-ing-hidden').value;
            if(!reqs) { alert("Selecciona al menos un líquido requerido."); return; }

            const recipeId = parseInt(document.getElementById('nr-id').value || '0');
            const servingModes = normalizeModeMap(collectServingModes(), selectedIngredients);

            const payload = {
                name: document.getElementById('nr-name').value,
                description: document.getElementById('nr-desc').value,
                ingredients: reqs,
                xp_reward: parseInt(document.getElementById('nr-xp').value),
                glass_options: selectedGlasses.slice(),
                serving_modes: servingModes,
            };
            
            try {
                if(recipeId > 0) {
                    await apiPost(`/api/admin/recipes/${recipeId}`, payload);
                } else {
                    await apiPost("/api/admin/recipes/create", payload);
                }
                resetRecipeForm();
                await loadAdminRecipes();
                await loadRecipes();
            } catch(e) { alert("Error al crear receta."); }
        }

        async function loadAdminRecipes() {
            try {
                const recipes = await apiGet("/api/admin/recipes");
                adminRecipesCache = recipes || [];
                const list = document.getElementById('admin-recipes-list');
                list.innerHTML = recipes.map(r => {
                    const glasses = (r.glass_options || []).join(', ') || '-';
                    const modes = Object.keys(r.serving_modes || {}).join(', ') || '-';
                    return `
                    <div style="display:flex; justify-content:space-between; padding:12px; background:var(--bg); border-radius:8px; margin-bottom:8px; border:1px solid var(--border);">
                        <div>
                            <strong style="color:var(--primary);">${r.name}</strong><br>
                            <span style="font-size:13px; color:var(--muted);">Reqs: ${r.ingredients}</span><br>
                            <span style="font-size:12px; color:var(--muted);">Vasos: ${glasses}</span><br>
                            <span style="font-size:12px; color:var(--muted);">Modos: ${modes}</span>
                        </div>
                        <div style="display:flex; gap:8px; align-items:flex-start;">
                            <button class="btn btn-small btn-secondary" onclick="editRecipe(${r.id})">Editar</button>
                            <button class="btn btn-small btn-danger" onclick="deleteRecipe(${r.id})">X</button>
                        </div>
                    </div>
                `;
                }).join('');
            } catch(e) {}
        }

        function editRecipe(id) {
            const recipe = (adminRecipesCache || []).find(r => Number(r.id) === Number(id));
            if(!recipe) return;

            document.getElementById('nr-id').value = recipe.id;
            document.getElementById('nr-name').value = recipe.name || '';
            document.getElementById('nr-desc').value = recipe.description || '';
            document.getElementById('nr-xp').value = recipe.xp_reward || 150;

            selectedIngredients = (recipe.ingredients || '')
                .split(',')
                .map(s => s.trim())
                .filter(Boolean);

            const availableGlasses = getRecipeGlassOptions(recipe);
            selectedGlasses = (recipe.glass_options && recipe.glass_options.length > 0)
                ? recipe.glass_options.filter(key => availableGlasses.includes(key))
                : availableGlasses.slice(0, 1);
            if(selectedGlasses.length === 0) selectedGlasses = availableGlasses.slice(0, 1);

            renderIngredientSelector();
            renderGlassSelector();
            renderServingModesEditor(recipe.serving_modes || {});

            document.getElementById('nr-submit').innerText = 'Guardar cambios';
            document.getElementById('add-recipe-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        async function deleteRecipe(id) {
            await fetch(`/api/admin/recipes/${id}`, {method: 'DELETE', headers: authHeaders()});
            if(parseInt(document.getElementById('nr-id').value || '0') === Number(id)) {
                resetRecipeForm();
            }
            await loadAdminRecipes();
            await loadRecipes();
        }

        // Ranking
        async function loadRanking() {
            const ranking = await apiGet("/api/users/ranking");
            document.getElementById("ranking-list").innerHTML = ranking.map((u, i) => {
                const avatar = u.avatar_url 
                    ? `<img src="${u.avatar_url}" style="width:36px; height:36px; border-radius:50%; object-fit:cover; border:2px solid var(--primary);">` 
                    : `<div style="width:36px; height:36px; border-radius:50%; background:var(--surface-2); display:flex; align-items:center; justify-content:center; font-size:18px;">👤</div>`;
                
                return `
                <tr>
                    <td style="width:50px;">${avatar}</td>
                    <td><strong>#${i+1}</strong></td>
                    <td class="rank-user" title="${u.full_name || u.username}">${u.full_name || u.username}</td>
                    <td class="rank-level-cell"><span class="rank-level-badge">LVL ${u.level}</span></td>
                    <td><strong>${u.xp}</strong></td>
                    <td><strong>${u.total_consumptions ?? 0}</strong></td>
                    <td>${u.most_consumed_recipe_name || u.favorite_recipe_name || '-'}</td>
                </tr>
                `;
            }).join("");
        }

        // Init
        async function init() {
            if (!getToken()) { window.location.href = "/"; return; }
            try { systemSettings = await apiGet("/api/admin/settings"); } catch(e) {}

            try {
                await loadProfile();
                await loadActiveGlasses();
                await pollMachineStatus(); 
                await loadRecipes();
                await loadGlobalHistory();
                await loadMyHistory();

                setInterval(pollMachineStatus, systemSettings.poll_status || 3000);
                setInterval(() => { if(!document.querySelector('select:focus')) renderTanks(); }, systemSettings.poll_tanks || 10000);
            } catch (e) {
                if (String(e) !== 'Error: unauthorized') {
                    console.error('Error iniciando dashboard', e);
                }
            }
        }

        window.onload = init;
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)