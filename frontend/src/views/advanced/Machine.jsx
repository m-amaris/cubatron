import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api'

export default function MachineView() {
  const [status, setStatus] = useState({ state: 'IDLE', levels: [], temperature: 0 })
  const [message, setMessage] = useState('')

  useEffect(() => { fetchStatus() }, [])

  async function fetchStatus() {
    try { const r = await api.get('/machine/status'); setStatus(r.data || {}) }
    catch (e) { setMessage('No se pudo obtener el estado de la máquina'); setTimeout(() => setMessage(''), 3000) }
  }

  async function doAction(action) {
    try {
      let res
      if (action === 'clean') res = await api.post('/machine/clean')
      else if (action === 'stop') res = await api.post('/machine/stop')
      else if (action === 'temp') res = await api.post('/machine/temp', { temperature: 30 })
      if (res && res.data && res.data.status) setMessage(`OK: ${res.data.status}`)
      await fetchStatus()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 3000)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu/avanzado" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Máquina</h2>
        <div className="w-8" />
      </div>

      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-sm text-gray-500">Estado</div>
          <div className="mt-2 text-xl font-semibold">{status.state}</div>
          <div className="text-xs text-gray-500">Temperatura: {status.temperature}</div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {status.levels.map((level, idx) => (
              <div key={idx} className="p-3 rounded-2xl bg-gray-50 border border-gray-100">
                <div className="text-xs text-gray-500">Depósito {idx + 1}</div>
                <div className="text-lg font-semibold">{level} ml</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => doAction('clean')} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Limpiar</button>
          <button onClick={() => doAction('stop')} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Parada emergencia</button>
          <button onClick={() => doAction('temp')} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Fijar 30°C</button>
          <button onClick={() => fetchStatus()} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Refrescar</button>
        </div>
        {message && <div className="text-sm text-indigo-700">{message}</div>}
      </div>
    </div>
  )
}
