"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { ChaptersPanel } from "@/components/ChaptersPanel"
import type { Summary } from "@/lib/api"

interface SummaryTabsProps {
  summary?: Summary
  isLoading: boolean
  courseId: number
  onSeek?: (timestamp: number) => void
}

export function SummaryTabs({ summary, isLoading, courseId, onSeek }: SummaryTabsProps) {
  const [activeTab, setActiveTab] = useState("abstract")

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
        <TabsTrigger value="abstract">摘要</TabsTrigger>
        <TabsTrigger value="notes">讲义</TabsTrigger>
        <TabsTrigger value="chapters">章节速览</TabsTrigger>
      </TabsList>
      <ScrollArea className="mt-4 flex-1">
        <TabsContent value="abstract" className="mt-0">
          <MarkdownContent content={summary.abstract || "暂无摘要"} />
        </TabsContent>
        <TabsContent value="notes" className="mt-0">
          <MarkdownContent content={summary.lecture_notes || "暂无讲义"} />
        </TabsContent>
        <TabsContent value="chapters" className="mt-0">
          <ChaptersPanel courseId={courseId} onSeek={onSeek} />
        </TabsContent>
      </ScrollArea>
    </Tabs>
  )
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  )
}
