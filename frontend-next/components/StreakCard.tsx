"use client"

import { Flame, CheckCircle2 } from "lucide-react"

import { Card } from "@/components/ui/card"
import { useStudyStats } from "@/hooks/use-api"

/** 学习打卡卡片：连续学习天数 + 今日状态 + 最近 30 天热力图。 */
export function StreakCard() {
  const { data } = useStudyStats()
  if (!data) return null

  const active = new Set(data.recent)
  // 最近 30 天（从今天往前），用于热力图
  const days: Date[] = []
  const today = new Date()
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    days.push(d)
  }

  return (
    <Card className="flex flex-wrap items-center gap-4 p-4">
      <div className="flex items-center gap-2">
        <Flame className={`h-6 w-6 ${data.streak > 0 ? "text-orange-500" : "text-muted-foreground"}`} />
        <div>
          <p className="text-2xl font-bold leading-none">{data.streak}</p>
          <p className="text-xs text-muted-foreground">连续学习天数</p>
        </div>
      </div>

      <div className="h-8 w-px bg-border" />

      <div>
        <p className="text-lg font-semibold leading-none">{data.total_days}</p>
        <p className="text-xs text-muted-foreground">累计学习天数</p>
      </div>

      <div className="h-8 w-px bg-border" />

      <div className={data.today_active ? "text-green-600 dark:text-green-400" : "text-muted-foreground"}>
        {data.today_active ? (
          <span className="flex items-center gap-1 text-sm font-medium">
            <CheckCircle2 className="h-4 w-4" /> 今日已学习
          </span>
        ) : (
          <span className="text-sm">今日还未学习，加油～</span>
        )}
      </div>

      {/* 最近 30 天热力图 */}
      <div className="ml-auto flex flex-wrap gap-1" title="最近 30 天学习情况">
        {days.map((d, i) => {
          const iso = d.toISOString().slice(0, 10)
          const on = active.has(iso)
          return (
            <div
              key={i}
              className={`h-3 w-3 rounded-sm ${on ? "bg-orange-400" : "bg-muted"}`}
              title={`${iso}${on ? " · 已学习" : ""}`}
            />
          )
        })}
      </div>
    </Card>
  )
}
