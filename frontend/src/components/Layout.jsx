import React from 'react'
import BottomNav from './BottomNav'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center">
      <main className="flex-1 w-full max-w-md p-4 pb-28">{children}</main>
      <BottomNav />
    </div>
  )
}
