import { Bot, User, AlertCircle } from "lucide-react"

import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import type { ChatMessage, ChatDebug } from "@/lib/api"

interface DebugChatProps {
  history: ChatMessage[]
  debug?: ChatDebug
  selectedMessageId: number | null
  onSelect: (messageId: number) => void
}

export function DebugChat({ history, debug, selectedMessageId, onSelect }: DebugChatProps) {
  const pairs: { user: ChatMessage; assistant: ChatMessage }[] = []
  for (let i = 0; i < history.length - 1; i++) {
    if (history[i].role === "user" && history[i + 1].role === "assistant") {
      pairs.push({ user: history[i], assistant: history[i + 1] })
      i++
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">课程问答记录</h3>
        {selectedMessageId && debug && (
          <div className="text-xs text-muted-foreground">
            已选：#{selectedMessageId} · {debug.model}
          </div>
        )}
      </div>

      <ScrollArea className="max-h-[400px]">
        <div className="space-y-4 pr-2">
          {pairs.length > 0 ? (
            pairs.map((pair) => (
              <QuestionPair
                key={pair.assistant.id}
                pair={pair}
                isSelected={pair.assistant.id === selectedMessageId}
                onSelect={() => pair.assistant.id && onSelect(pair.assistant.id)}
              />
            ))
          ) : (
            <div className="flex flex-col items-center justify-center rounded-xl border py-10 text-center">
              <AlertCircle className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">该课程暂无问答记录。先去提问，再来诊断。</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

function QuestionPair({
  pair,
  isSelected,
  onSelect,
}: {
  pair: { user: ChatMessage; assistant: ChatMessage }
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <div
      className={`rounded-lg border p-3 transition-colors ${
        isSelected ? "border-primary bg-primary/5" : "hover:bg-accent/50"
      }`}
    >
      <div className="mb-2 flex items-start gap-2">
        <User className="mt-0.5 h-4 w-4 text-muted-foreground" />
        <p className="flex-1 text-sm font-medium">{pair.user.content}</p>
      </div>
      <div className="mb-2 flex items-start gap-2">
        <Bot className="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div className="flex-1 text-sm">
          <MarkdownRenderer>{pair.assistant.content}</MarkdownRenderer>
        </div>
      </div>
      {pair.assistant.id && (
        <Button variant="outline" size="sm" onClick={onSelect}>
          {isSelected ? "已选中" : "查看诊断"}
        </Button>
      )}
    </div>
  )
}
