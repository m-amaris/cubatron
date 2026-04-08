const tokenKey = 'cubatron_token';

function bindLoginForm() {
  const loginForm = document.getElementById('loginForm');
  if (!loginForm) {
    return;
  }

  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.access_token) {
      document.getElementById('loginMsg').innerText = data.detail || 'Login incorrecto';
      return;
    }

    sessionStorage.setItem(tokenKey, data.access_token);
    window.location.href = '/dashboard';
  });
}

document.addEventListener('DOMContentLoaded', bindLoginForm);
