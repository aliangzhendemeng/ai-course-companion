import Link from "next/link"
import { usePathname } from "next/navigation"
import { BookOpen, MessageCircle, Library, GraduationCap, Settings, History } from "lucide-react"

import { cn } from "@/lib/utils"

const navItems = [
  { href: "/courses", label: "课程库", icon: Library },
  { href: "/chat", label: "全局搜索", icon: MessageCircle },
  { href: "/history", label: "问答历史", icon: History },
  { href: "/settings", label: "设置", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-border bg-card shadow-sm">
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
          <GraduationCap className="h-5 w-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-base font-bold leading-tight text-foreground">AI 慕课学伴</span>
          <span className="text-[10px] leading-tight text-muted-foreground">智能学习助手</span>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          菜单
        </p>
        {navItems.map((item) => {
          const Icon = item.icon
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className={cn("h-4 w-4 transition-colors", active ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground")} />
              {item.label}
              {active && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary-foreground" />
              )}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-border p-4">
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-xs font-medium text-foreground">AI 慕课学伴</p>
          <p className="mt-1 text-[10px] leading-relaxed text-muted-foreground">
            基于 AI 的视频课程学习与知识问答平台
          </p>
        </div>
      </div>
    </aside>
  )
}
