import React, { useEffect, useState } from 'react'
import api from '../services/api'
import Header from '../components/Header'
import ProgressCard from '../components/ProgressCard'
import StatCard from '../components/StatCard'
import LevelCard from '../components/LevelCard'
import CalendarStrip from '../components/CalendarStrip'
import ActivityFeed from '../components/ActivityFeed'

export default function Home() {
  const [history, setHistory] = useState([])

  useEffect(() => {
    let cancelled = false
    api.get('/history?limit=100')
      .then(res => {
        if (!cancelled) setHistory(res.data || [])
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [])

  const daysThisWeek = Math.min(7, history.length)

  // Calculate water consumptions in the last 24 hours
  const now = new Date()
  const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000)
  const drinkCountLast24h = history.filter(h => {
    if (!h.created_at) return false
    const createdDate = new Date(h.created_at)
    return createdDate >= last24h && createdDate <= now
  }).length

  // Determine most-taken recipe in the last 7 days; fallback to historical
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  const recentRecipes = history.filter(h => {
    if (!h.created_at || !h.recipe_name) return false
    const createdDate = new Date(h.created_at)
    return createdDate >= sevenDaysAgo && createdDate <= now
  })

  const selectedForCounting = recentRecipes.length ? recentRecipes : history.filter(h => h.recipe_name)
  const recipeCounts = selectedForCounting.reduce((acc, h) => {
    acc[h.recipe_name] = (acc[h.recipe_name] || 0) + 1
    return acc
  }, {})

  const mostTakenEntry = Object.entries(recipeCounts).sort((a, b) => b[1] - a[1])[0] || null
  const mostTakenRecipeName = mostTakenEntry ? mostTakenEntry[0] : 'Sin datos'
  const mostTakenRecipeCount = mostTakenEntry ? mostTakenEntry[1] : 0

  return (
    <div>
      <Header username="Sajibur Rahman" />

      <section className="mb-4">
        <ProgressCard days={daysThisWeek} goal={7} />
      </section>

      <section className="mb-4">
        <div className="flex gap-3">
          <StatCard
            title={<>Tu gusto<br />últimamente</>}
            value={mostTakenRecipeName}
            unit={mostTakenRecipeCount ? `${mostTakenRecipeCount} veces` : ''}
          />
          <StatCard title="Últimas 24h" value={drinkCountLast24h} unit="consumiciones" />
          <LevelCard xp={history.reduce((s, h) => s + (h.xp_gained || 0), 0) || 0} />
        </div>
      </section>

      <section className="mb-4">
        <div className="rounded-2xl overflow-hidden bg-white text-gray-800 shadow-lg border border-gray-100 p-4 animate-fade-in-up">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">Calendario</h3>
            <div className="text-xs text-gray-500">Últimos 15 días</div>
          </div>
          <CalendarStrip />
        </div>
      </section>

      <section>
        <h3 className="font-semibold mb-3">Recent activity</h3>
        <ActivityFeed items={history} />
      </section>
    </div>
  )
}
