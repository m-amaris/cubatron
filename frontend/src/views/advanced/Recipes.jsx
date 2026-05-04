import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api'

export default function RecipesView() {
  const [recipes, setRecipes] = useState([])
  const [newRecipe, setNewRecipe] = useState({ name: '', description: '', composition: '{"1":50,"2":50}' })
  const [message, setMessage] = useState('')

  useEffect(() => { fetchRecipes() }, [])

  async function fetchRecipes() {
    try { const r = await api.get('/drinks'); setRecipes(r.data || []) }
    catch (e) { setRecipes([]) }
  }

  async function createRecipe() {
    let composition
    try { composition = JSON.parse(newRecipe.composition) }
    catch (e) { setMessage('Composición inválida'); setTimeout(()=>setMessage(''),3000); return }
    try { await api.post('/drinks', { name: newRecipe.name, description: newRecipe.description, composition }); setNewRecipe({ name: '', description: '', composition: '{"1":50,"2":50}' }); setMessage('Receta creada'); fetchRecipes() }
    catch (err) { setMessage('Error: '+(err.response?.data?.detail||err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  async function removeRecipe(id) {
    if (!window.confirm('Eliminar receta?')) return
    try { await api.delete(`/drinks/${id}`); setMessage('Receta eliminada'); fetchRecipes() }
    catch (err) { setMessage('Error: '+(err.response?.data?.detail||err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu/avanzado" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Gestión de recetas</h2>
        <div className="w-8" />
      </div>

      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-sm font-medium mb-2">Nueva receta</div>
          <div>
            <input placeholder="Nombre" value={newRecipe.name} onChange={e=>setNewRecipe(p=>({...p,name:e.target.value}))} className="w-full p-3 rounded-2xl border border-gray-100 mb-2" />
            <input placeholder="Descripción" value={newRecipe.description} onChange={e=>setNewRecipe(p=>({...p,description:e.target.value}))} className="w-full p-3 rounded-2xl border border-gray-100 mb-2" />
            <textarea placeholder='Composición JSON' value={newRecipe.composition} onChange={e=>setNewRecipe(p=>({...p,composition:e.target.value}))} rows={4} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <button onClick={createRecipe} className="w-full mt-3 py-3 rounded-3xl bg-indigo-700 text-white">Agregar receta</button>
        </div>

        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Recetas</div>
          {recipes.map(r => (
            <div key={r.id} className="rounded-2xl border border-gray-100 p-3 flex items-center justify-between">
              <div>
                <div className="font-medium">{r.name}</div>
                <div className="text-xs text-gray-500">{r.description}</div>
                <div className="text-xs text-gray-500">{JSON.stringify(r.composition)}</div>
              </div>
              <div className="flex gap-2">
                <button onClick={()=>removeRecipe(r.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Eliminar</button>
              </div>
            </div>
          ))}
        </div>
      </div>
      {message && <div className="text-sm text-green-700">{message}</div>}
    </div>
  )
}
