import React from 'react'
import { Routes, Route } from 'react-router-dom'
import AppRoutes from './AppRoutes'
import Login from './views/Login'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<AppRoutes />} />
    </Routes>
  )
}
