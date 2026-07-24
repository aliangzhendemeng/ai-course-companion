"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { BookOpen, MessageCircle, Library } from "lucide-react"

import { cn } from "@/lib/utils"

const navItems = [
  { href: "/courses", label: "课程库", icon: Library },
  { href: "/chat", label: "知识问答", icon: MessageCircle },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r bg-card">
      <div className="flex items-center gap-2 border-b p-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <BookOpen className="h-5 w-5" />
        </div>
        <span className="text-lg font-bold text-foreground">AI 慕课学伴</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t p-4 text-xs text-muted-foreground">
        © 2026 AI 慕课学伴
      </div>
    </aside>
  )
}
