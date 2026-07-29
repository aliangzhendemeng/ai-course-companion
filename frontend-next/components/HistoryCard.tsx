import { Trash2, MessageSquare, Globe, BookOpen, User, Bot } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { deduplicateSources, formatTimestamp } from "@/lib/timestamp"
import type { HistoryItem, Source } from "@/lib/api"

export interface QAPair {
  question?: HistoryItem
  answer?: HistoryItem
}

interface HistoryCardProps {
  pair: QAPair
  onDelete?: (id: number) => void
  onDebug?: (id: number) => void
}

export function HistoryCard({ pair, onDelete, onDebug }: HistoryCardProps) {
  const answer = pair.answer
  const isGlobal = (answer?.scope ?? pair.question?.scope) === "all"
  const courseTitle = answer?.course_title ?? pair.question?.course_title
  const sourceGroups = answer ? deduplicateSources(normalizeSources(answer.sources)) : []
  const createdAt = answer?.created_at ?? pair.question?.created_at

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge variant={isGlobal ? "default" : "secondary"} className="gap-1">
              {isGlobal ? <Globe className="h-3 w-3" /> : <BookOpen className="h-3 w-3" />}
              {isGlobal ? "全局搜索" : "课程问答"}
            </Badge>
            {courseTitle && (
              <span className="text-sm text-muted-foreground">{courseTitle}</span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {answer?.id && onDebug && (
              <Button variant="ghost" size="sm" onClick={() => onDebug(answer.id!)}>
                <MessageSquare className="mr-1 h-4 w-4" />
                诊断
              </Button>
            )}
            {(answer?.id ?? pair.question?.id) && onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive"
                onClick={() => {
                  const ids = [pair.question?.id, answer?.id].filter(Boolean) as number[]
                  ids.forEach(onDelete)
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {pair.question ? (
          <div className="flex gap-2">
            <User className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <p className="text-sm font-medium">{pair.question.content}</p>
          </div>
        ) : null}

        {answer ? (
          <div className="flex gap-2">
            <Bot className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="min-w-0 flex-1 text-sm">
              <MarkdownRenderer>{answer.content}</MarkdownRenderer>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">（无回答记录）</p>
        )}

        {sourceGroups.length > 0 && (
          <div className="ml-6">
            <p className="mb-1 text-xs font-medium text-muted-foreground">参考来源</p>
            <div className="flex flex-wrap gap-2">
              {sourceGroups.map((group, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground"
                  title={group.sources[0]?.text}
                >
                  {group.courseTitle && <span className="mr-1">{group.courseTitle} · </span>}
                  {formatTimestamp(group.timestamp)}
                  {group.sources.length > 1 && (
                    <span className="ml-1 text-[10px] opacity-80">({group.sources.length} 个来源)</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>

      {createdAt && (
        <CardFooter className="pt-0">
          <p className="text-xs text-muted-foreground">{new Date(createdAt).toLocaleString("zh-CN")}</p>
        </CardFooter>
      )}
    </Card>
  )
}

function normalizeSources(sources: HistoryItem["sources"]): Source[] {
  if (!sources) return []
  if (Array.isArray(sources)) return sources
  if (typeof sources === "string") {
    try {
      const parsed = JSON.parse(sources)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}
