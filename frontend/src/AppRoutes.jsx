import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './views/Home'
import Recipes from './views/Recipes'
import MenuIndex from './views/MenuIndex'
import { ProfileSection, AccountSection, AppearanceSection, NotificationsSection, AdvancedSection } from './views/Menu'

export default function AppRoutes() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/recipes" element={<ProtectedRoute><Recipes /></ProtectedRoute>} />
        <Route path="/menu" element={<ProtectedRoute><MenuIndex /></ProtectedRoute>} />
        <Route path="/menu/perfil" element={<ProtectedRoute><ProfileSection /></ProtectedRoute>} />
        <Route path="/menu/cuenta" element={<ProtectedRoute><AccountSection /></ProtectedRoute>} />
        <Route path="/menu/apariencia" element={<ProtectedRoute><AppearanceSection /></ProtectedRoute>} />
        <Route path="/menu/notificaciones" element={<ProtectedRoute><NotificationsSection /></ProtectedRoute>} />
        <Route path="/menu/avanzado" element={<ProtectedRoute><AdvancedSection /></ProtectedRoute>} />
        <Route path="/menu/avanzado/:section" element={<ProtectedRoute><AdvancedSection /></ProtectedRoute>} />
      </Routes>
    </Layout>
  )
}