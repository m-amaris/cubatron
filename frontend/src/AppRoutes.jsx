import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './views/Home'
import Recipes from './views/Recipes'
import MenuIndex from './views/MenuIndex'
import { ProfileSection, AccountSection, AppearanceSection, NotificationsSection } from './views/Menu'
import AdvancedIndex from './views/advanced/Index'
import MachineView from './views/advanced/Machine'
import UsersView from './views/advanced/Users'
import RecipesView from './views/advanced/Recipes'
import CupsView from './views/advanced/Cups'
import DepositsView from './views/advanced/Deposits'
import IngredientsView from './views/advanced/Ingredients'

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
        <Route path="/menu/avanzado" element={<ProtectedRoute><AdvancedIndex /></ProtectedRoute>} />
        <Route path="/menu/avanzado/machine" element={<ProtectedRoute><MachineView /></ProtectedRoute>} />
        <Route path="/menu/avanzado/users" element={<ProtectedRoute><UsersView /></ProtectedRoute>} />
        <Route path="/menu/avanzado/recipes" element={<ProtectedRoute><RecipesView /></ProtectedRoute>} />
        <Route path="/menu/avanzado/cups" element={<ProtectedRoute><CupsView /></ProtectedRoute>} />
        <Route path="/menu/avanzado/deposits" element={<ProtectedRoute><DepositsView /></ProtectedRoute>} />
        <Route path="/menu/avanzado/ingredients" element={<ProtectedRoute><IngredientsView /></ProtectedRoute>} />
      </Routes>
    </Layout>
  )
}
