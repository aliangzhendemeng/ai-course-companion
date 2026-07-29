import ReactMarkdown from "react-markdown"

import { ScrollArea } from "@/components/ui/scroll-area"
import type { SummaryDebug } from "@/lib/api"

interface DebugSummaryProps {
  summary?: SummaryDebug
}

export function DebugSummary({ summary }: DebugSummaryProps) {
  if (!summary) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl border text-sm text-muted-foreground">
        暂无总结数据。
      </div>
    )
  }

  const sections = [
    { key: "outline", title: "大纲", content: summary.outline },
    { key: "abstract", title: "摘要", content: summary.abstract },
    { key: "lecture_notes", title: "讲义", content: summary.lecture_notes },
  ]

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <div key={section.key}>
          <h3 className="mb-2 text-sm font-semibold">{section.title}</h3>
          {section.content ? (
            <ScrollArea className="max-h-[240px] rounded-md border bg-muted p-3">
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{section.content}</ReactMarkdown>
              </div>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground">无{section.title}内容。</p>
          )}
        </div>
      ))}
    </div>
  )
}
