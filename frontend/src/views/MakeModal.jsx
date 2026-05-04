import React, { useEffect, useState, useRef } from 'react'
import api from '../services/api'

function ModeSelector({ mode, setMode }) {
  const modes = ['low', 'medium', 'high', 'extreme', 'custom']
  return (
    <div className="flex gap-2">
      {modes.map(m => (
        <button key={m} onClick={() => setMode(m)} className={`px-3 py-1 rounded ${mode===m? 'bg-indigo-600 text-white': 'bg-gray-200'}`}>{m}</button>
      ))}
    </div>
  )
}

export default function MakeModal({ onClose, initialRecipe = null }) {
  const [recipes, setRecipes] = useState([])
  const [cups, setCups] = useState([])
  const [selectedRecipe, setSelectedRecipe] = useState(initialRecipe)
  const [selectedCup, setSelectedCup] = useState(null)
  const [mode, setMode] = useState('medium')
  const [customMl, setCustomMl] = useState(200)
  const [status, setStatus] = useState(null)
  const [progress, setProgress] = useState(0)
  const pollRef = useRef(null)

  useEffect(() => {
    api.get('/drinks').then(r => setRecipes(r.data || [])).catch(() => {})
    api.get('/cups').then(r => setCups(r.data || [])).catch(() => {})
  }, [])

  // if an initial recipe was passed, set it once recipes are loaded
  useEffect(() => {
    if (!initialRecipe) return
    if (recipes && recipes.length) {
      const found = recipes.find(r => r.id === initialRecipe.id || String(r.id) === String(initialRecipe.id))
      if (found) setSelectedRecipe(found)
      else setSelectedRecipe(initialRecipe)
    }
  }, [initialRecipe, recipes])

  const startPolling = () => {
    setProgress(0)
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.get('/machine/status')
        setStatus(res.data)
        if (res.data.state === 'IDLE') {
          clearInterval(pollRef.current)
          setProgress(100)
          // fetch latest history to show XP gained
          try {
            const hres = await api.get('/history?limit=1')
            if (hres.data && hres.data.length > 0) {
              const latest = hres.data[0]
              alert(`Drink complete. XP gained: ${latest.xp_gained || 0}`)
            }
          } catch (e) {
            // ignore
          }
        } else {
          setProgress(p => Math.min(99, p + 10))
        }
      } catch (err) {
        // ignore
      }
    }, 2000)
  }

  const handleMake = async () => {
    if (!selectedRecipe || !selectedCup) return alert('Select recipe and cup')
    const payload = {
      recipe_id: selectedRecipe.id,
      cup_id: selectedCup.id,
      mode: mode,
      custom_ml: mode === 'custom' ? Number(customMl) : undefined
    }
    try {
      const res = await api.post('/drinks/make', payload)
      // start polling
      startPolling()
      // optimistic progress
    } catch (err) {
      if (err.response && err.response.status === 409) {
        alert('Machine is busy. Try again later.')
      } else {
        alert('Failed to start')
      }
    }
  }

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-lg p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold">Prepare drink</h3>
          <button onClick={onClose} className="text-gray-500">Close</button>
        </div>

        <div className="mb-3">
          <label className="block text-sm text-gray-600">Recipe</label>
          <select
            className="w-full p-2 border rounded"
            value={selectedRecipe ? String(selectedRecipe.id) : ''}
            onChange={e => setSelectedRecipe(recipes.find(r => String(r.id) === e.target.value))}
          >
            <option value="">-- select --</option>
            {recipes.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
          </select>
        </div>

        <div className="mb-3">
          <label className="block text-sm text-gray-600">Cup</label>
          <select
            className="w-full p-2 border rounded"
            value={selectedCup ? String(selectedCup.id) : ''}
            onChange={e => setSelectedCup(cups.find(c => String(c.id) === e.target.value))}
          >
            <option value="">-- select --</option>
            {cups.map(c => <option key={c.id} value={String(c.id)}>{c.name} ({c.capacity_ml} ml)</option>)}
          </select>
        </div>

        <div className="mb-3">
          <label className="block text-sm text-gray-600">Mode</label>
          <ModeSelector mode={mode} setMode={setMode} />
        </div>

        {mode === 'custom' && (
          <div className="mb-3">
            <label className="block text-sm text-gray-600">Custom ML</label>
            <input type="number" value={customMl} onChange={e=>setCustomMl(e.target.value)} className="w-full p-2 border rounded" />
          </div>
        )}

        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-3 py-1">Cancel</button>
          <button onClick={handleMake} className="px-3 py-1 bg-indigo-600 text-white rounded">Start</button>
        </div>

        {status && (
          <div className="mt-4">
            <div className="h-2 bg-gray-200 rounded overflow-hidden">
              <div className="h-full bg-indigo-500" style={{width: `${progress}%`}} />
            </div>
            <div className="text-sm text-gray-600 mt-1">State: {status.state} — {status.message || ''}</div>
          </div>
        )}
      </div>
    </div>
  )
}
