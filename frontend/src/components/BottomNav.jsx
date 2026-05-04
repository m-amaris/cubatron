import React from 'react'
import { Link } from 'react-router-dom'

function Icon({ children, label }) {
  return (
    <div className="flex flex-col items-center text-gray-600 text-xs">
      <div className="w-6 h-6">{children}</div>
      <div className="mt-1" aria-hidden>{label}</div>
    </div>
  )
}

export default function BottomNav() {
  return (
    <nav className="fixed bottom-4 left-1/2 transform -translate-x-1/2 w-full max-w-md px-4 z-50">
      <div className="bg-white rounded-full shadow-lg px-4 py-2 flex items-center justify-between">
        <Link to="/" className="flex-1 flex items-center justify-center">
          <Icon label="Home">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M3 11.5L12 4l9 7.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V11.5z" />
              <path d="M9 21v-6h6v6" />
            </svg>
          </Icon>
        </Link>

        <Link to="/stats" className="flex-1 flex items-center justify-center">
          <Icon label="Stats">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M3 3v18h18" />
              <rect x="7" y="9" width="3" height="6" rx="1" />
              <rect x="13" y="6" width="3" height="9" rx="1" />
              <rect x="18" y="12" width="3" height="3" rx="1" />
            </svg>
          </Icon>
        </Link>

        <Link to="/recipes" aria-label="Prepare drink" className="mx-2 bg-gradient-to-br from-indigo-600 to-green-400 text-white rounded-full w-16 h-16 -mt-8 shadow-xl flex items-center justify-center">
          <svg viewBox="0 0 24 24" width="28" height="28" className="w-7 h-7" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 3h18L12 13 3 3z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <path d="M12 13v6" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M8 21h8" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="18.5" cy="4.5" r="1" fill="white" />
          </svg>
        </Link>

        <Link to="/friends" className="flex-1 flex items-center justify-center">
          <Icon label="Friends">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 00-3-3.87" />
              <path d="M16 3.13a4 4 0 010 7.75" />
            </svg>
          </Icon>
        </Link>

        <Link to="/menu" className="flex-1 flex items-center justify-center">
          <Icon label="Menu">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M4 6h16" />
              <path d="M4 12h16" />
              <path d="M4 18h16" />
            </svg>
          </Icon>
        </Link>
      </div>
    </nav>
  )
}
