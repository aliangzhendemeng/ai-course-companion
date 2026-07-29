"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import type { Summary } from "@/lib/api"

interface SummaryTabsProps {
  summary?: Summary
  isLoading: boolean
  onSeek?: (timestamp: number) => void
}

export function SummaryTabs({ summary, isLoading, onSeek }: SummaryTabsProps) {
  const [activeTab, setActiveTab] = useState("outline")

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl border text-sm text-muted-foreground">
        暂无总结，请等待课程处理完成。
      </div>
    )
  }

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex h-full flex-col">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="outline">大纲</TabsTrigger>
        <TabsTrigger value="abstract">摘要</TabsTrigger>
        <TabsTrigger value="notes">讲义</TabsTrigger>
      </TabsList>
      <ScrollArea className="mt-4 flex-1">
        <TabsContent value="outline" className="mt-0">
          <OutlineContent outline={summary.outline || ""} onSeek={onSeek} />
        </TabsContent>
        <TabsContent value="abstract" className="mt-0">
          <MarkdownContent content={summary.abstract || "暂无摘要"} />
        </TabsContent>
        <TabsContent value="notes" className="mt-0">
          <MarkdownContent content={summary.lecture_notes || "暂无讲义"} />
        </TabsContent>
      </ScrollArea>
    </Tabs>
  )
}

function OutlineContent({ outline, onSeek }: { outline: string; onSeek?: (timestamp: number) => void }) {
  const lines = outline.split("\n").filter(Boolean)
  return (
    <ul className="space-y-2">
      {lines.map((line, idx) => {
        const match = line.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*[\-\.]?\s*(.*)$/)
        if (match) {
          const h = parseInt(match[1], 10)
          const m = parseInt(match[2], 10)
          const s = match[3] ? parseInt(match[3], 10) : 0
          const seconds = h * 3600 + m * 60 + s
          const text = match[4] || line
          return (
            <li key={idx}>
              <button
                onClick={() => onSeek?.(seconds)}
                className="text-left text-sm text-accent hover:underline"
              >
                {line.trim()}
              </button>
            </li>
          )
        }
        return (
          <li key={idx} className="text-sm text-foreground">{line.trim()}</li>
        )
      })}
    </ul>
  )
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  )
}
