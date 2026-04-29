import React, { useState } from 'react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || !data.access_token) {
        setMsg(data.detail || 'Login incorrecto')
        return
      }
      sessionStorage.setItem('cubatron_token', data.access_token)
      window.location.href = '/dashboard'
    } catch (err) {
      setMsg('Error de red')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-6 bg-white rounded shadow w-full max-w-md">
        <h1 className="text-2xl font-semibold mb-4">Cubatron</h1>
        <form onSubmit={handleSubmit}>
          <input className="w-full mb-2 p-2 border rounded" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Usuario" />
          <input type="password" className="w-full mb-2 p-2 border rounded" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Contraseña" />
          <button className="w-full bg-emerald-600 text-white py-2 rounded" type="submit">Entrar</button>
        </form>
        {msg && <p className="mt-2 text-red-600">{msg}</p>}
      </div>
    </div>
  )
}
