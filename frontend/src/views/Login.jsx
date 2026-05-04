import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await api.post('/auth/login', { username, password })
      localStorage.setItem('token', response.data.access_token)
      try {
        const profileResp = await api.get('/users/me')
        localStorage.setItem('cubatron_profile', JSON.stringify(profileResp.data))
      } catch (profileErr) {
        console.error('Error fetching profile:', profileErr)
      }
      navigate('/')
    } catch (err) {
      setError('Credenciales inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm bg-white border border-slate-200 shadow-xl shadow-slate-200/40 rounded-3xl p-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Cubatron</h1>
          <p className="mt-2 text-sm text-slate-500">Controla tu máquina de coctelería desde el móvil.</p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="sr-only">Usuario</label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="block w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:ring-indigo-500"
                placeholder="Usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Contraseña</label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="block w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:ring-indigo-500"
                placeholder="Contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full rounded-2xl py-3 text-sm font-semibold text-white shadow-lg transition focus:outline-none focus:ring-4 ${loading ? 'bg-indigo-400 cursor-not-allowed shadow-none' : 'bg-gradient-to-r from-indigo-600 to-violet-600 shadow-violet-500/20 hover:scale-[1.01] focus:ring-indigo-200'}`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Cargando...
                </span>
              ) : (
                'Iniciar sesión'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}