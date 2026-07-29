"use client"

import { Sidebar } from "@/components/Sidebar"

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 min-h-screen flex-1 bg-background">{children}</main>
    </div>
  )
}
