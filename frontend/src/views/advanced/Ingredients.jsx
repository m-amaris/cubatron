import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api'

export default function IngredientsView() {
  const [ingredients, setIngredients] = useState([])
  const [newIngredient, setNewIngredient] = useState({ name: '', description: '' })
  const [message, setMessage] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editFields, setEditFields] = useState({ name: '', description: '' })

  useEffect(() => { fetchIngredients() }, [])

  async function fetchIngredients() {
    try { const r = await api.get('/ingredients'); setIngredients(r.data || []) }
    catch (e) { setIngredients([]) }
  }

  async function createIngredient() {
    if (!newIngredient.name) { setMessage('El nombre es obligatorio'); setTimeout(() => setMessage(''), 3000); return }
    try {
      await api.post('/ingredients', newIngredient)
      setNewIngredient({ name: '', description: '' })
      setMessage('Ingrediente creado')
      fetchIngredients()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  function startEdit(ing) {
    setEditingId(ing.id)
    setEditFields({ name: ing.name || '', description: ing.description || '' })
  }

  function cancelEdit() {
    setEditingId(null)
    setEditFields({ name: '', description: '' })
  }

  async function saveEdit(ingredientId) {
    const original = ingredients.find(i => i.id === ingredientId) || {}
    const payload = {}
    if (editFields.name && editFields.name !== original.name) payload.name = editFields.name
    if (editFields.description !== original.description) payload.description = editFields.description
    if (Object.keys(payload).length === 0) { setMessage('No hay cambios'); setTimeout(() => setMessage(''), 2000); return }
    try {
      await api.patch(`/ingredients/${ingredientId}`, payload)
      setMessage('Ingrediente actualizado')
      cancelEdit()
      fetchIngredients()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function removeIngredient(id) {
    if (!window.confirm('¿Eliminar ingrediente?')) return
    try { await api.delete(`/ingredients/${id}`); setMessage('Ingrediente eliminado'); fetchIngredients() }
    catch (err) { setMessage('Error: ' + (err.response?.data?.detail || err.message)) }
    setTimeout(() => setMessage(''), 3000)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu/avanzado" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Líquidos</h2>
        <div className="w-8" />
      </div>

      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-sm font-medium mb-2">Nuevo líquido</div>
          <input
            placeholder="Nombre del ingrediente"
            value={newIngredient.name}
            onChange={e => setNewIngredient(p => ({ ...p, name: e.target.value }))}
            className="w-full p-3 rounded-2xl border border-gray-100 mb-2"
          />
          <input
            placeholder="Descripción (opcional)"
            value={newIngredient.description}
            onChange={e => setNewIngredient(p => ({ ...p, description: e.target.value }))}
            className="w-full p-3 rounded-2xl border border-gray-100"
          />
          <button onClick={createIngredient} className="w-full mt-3 py-3 rounded-3xl bg-indigo-700 text-white">
            Agregar líquido
          </button>
        </div>

        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Líquidos registrados</div>
          {ingredients.length === 0 ? (
            <div className="text-sm text-gray-500">No hay líquidos registrados.</div>
          ) : (
            ingredients.map(ing => (
              <div key={ing.id} className="rounded-2xl border border-gray-100 p-3">
                {editingId === ing.id ? (
                  <div className="space-y-2">
                    <input
                      value={editFields.name}
                      onChange={e => setEditFields(p => ({ ...p, name: e.target.value }))}
                      className="w-full p-2 rounded-2xl border border-gray-100"
                      placeholder="Nombre"
                    />
                    <input
                      value={editFields.description}
                      onChange={e => setEditFields(p => ({ ...p, description: e.target.value }))}
                      className="w-full p-2 rounded-2xl border border-gray-100"
                      placeholder="Descripción"
                    />
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(ing.id)} className="px-3 py-2 rounded-2xl bg-indigo-700 text-white text-xs">Guardar</button>
                      <button onClick={cancelEdit} className="px-3 py-2 rounded-2xl bg-gray-100 text-xs">Cancelar</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{ing.name}</div>
                      <div className="text-xs text-gray-500">{ing.description || 'Sin descripción'}</div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => startEdit(ing)} className="px-3 py-2 rounded-2xl bg-yellow-100 text-yellow-700 text-xs">Editar</button>
                      <button onClick={() => removeIngredient(ing.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Eliminar</button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
      {message && <div className="text-sm text-green-700 mt-3">{message}</div>}
    </div>
  )
}
