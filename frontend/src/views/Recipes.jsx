import React, { useEffect, useState } from 'react'
import api from '../services/api'
import { Link } from 'react-router-dom'
import MakeModal from './MakeModal'

function CategoryPills({ categories, active, setActive }) {
  return (
    <div className="flex gap-2 overflow-x-auto py-2">
      {categories.map(c => (
        <button key={c} onClick={() => setActive(c)} className={`px-3 py-1 rounded-full ${active===c? 'bg-gray-900 text-white' : 'bg-white/60 text-gray-700'}`}>
          {c}
        </button>
      ))}
    </div>
  )
}

function RecipeCard({ recipe, onPrepare }) {
  const ratingVal = recipe.rating ?? recipe.avg_rating ?? recipe.average_rating ?? null
  const ratingDisplay = ratingVal !== null && typeof ratingVal !== 'undefined' ? `${Number(ratingVal).toFixed(1)} ★` : 'Sin valoración'
  return (
    <div className="block bg-white rounded-2xl p-3 flex items-center justify-between border border-gray-100 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center text-green-700 font-semibold">{(recipe.name||'')[0]}</div>
        <div>
          <div className="font-medium text-gray-800">{recipe.name}</div>
          <div className="text-xs text-gray-400 mt-1">{recipe.description || ''}</div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-gray-400">
          <div className="text-sm">{ratingDisplay}</div>
        </div>
        <button onClick={e => { e.stopPropagation(); onPrepare && onPrepare() }} className="px-3 py-1 bg-indigo-600 text-white rounded">Preparar</button>
      </div>
    </div>
  )
}

export default function Recipes() {
  const [recipes, setRecipes] = useState([])
  const [query, setQuery] = useState('')
  const [activeCat, setActiveCat] = useState('All')
  const [showMakeModal, setShowMakeModal] = useState(false)
  const [prepRecipe, setPrepRecipe] = useState(null)

  const categories = ['All', 'Breakfast', 'Lunch', 'Dinner', 'Snack']

  useEffect(() => {
    let cancelled = false
    api.get('/drinks').then(res => { if(!cancelled) setRecipes(res.data || []) }).catch(()=>{})
    return () => { cancelled = true }
  }, [])

  const filtered = recipes.filter(r => {
    if (activeCat !== 'All') return r.name && r.name.toLowerCase().includes(activeCat.toLowerCase())
    if (!query) return true
    return (r.name || '').toLowerCase().includes(query.toLowerCase())
  })

  return (
    <div>
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <Link to="/" className="p-2 bg-white rounded-full shadow-sm">←</Link>
          <h2 className="text-lg font-semibold">All recipes</h2>
          <div className="w-8" />
        </div>

        <div className="mb-3">
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search here" className="w-full p-3 rounded-full bg-white shadow-sm" />
        </div>

        <CategoryPills categories={categories} active={activeCat} setActive={setActiveCat} />
      </div>

      <div className="space-y-3">
        {filtered.map(r => <RecipeCard key={r.id} recipe={r} onPrepare={() => { setPrepRecipe(r); setShowMakeModal(true) }} />)}
      </div>

      {showMakeModal && (
        <MakeModal
          initialRecipe={prepRecipe}
          onClose={() => { setShowMakeModal(false); setPrepRecipe(null) }}
        />
      )}
    </div>
  )
}
