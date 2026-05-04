import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './api' // Configure axios
import './styles/index.css'

// Initialize theme early so the correct colors load before React renders
try {
  const s = localStorage.getItem('cubatron_theme') || 'light'
  const a = localStorage.getItem('cubatron_accent') || '#6366f1'
  document.documentElement.setAttribute('data-theme', s)
  document.documentElement.style.setProperty('--accent-color', a)
} catch (e) {
  // ignore (e.g., during SSR or if localStorage not available)
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
