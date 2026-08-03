"use client"

import { useState } from "react"
import { Check, Pencil, Plus, Trash2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  useConversations,
  useDeleteConversation,
  useRenameConversation,
} from "@/hooks/use-api"

interface ConversationSwitcherProps {
  courseId: number
  activeId: number | null
  onSelect: (id: number | null) => void
}

/** 会话切换器：下拉选会话 + 新建 + 改名 + 删除。 */
export function ConversationSwitcher({ courseId, activeId, onSelect }: ConversationSwitcherProps) {
  const { data: convs } = useConversations(courseId)
  const deleteMut = useDeleteConversation()
  const renameMut = useRenameConversation()
  const list = convs ?? []
  const current = list.find((c) => c.id === activeId)

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState("")

  const startRename = () => {
    setDraft(current?.title ?? "")
    setEditing(true)
  }
  const saveRename = () => {
    const t = draft.trim()
    if (t && activeId !== null) {
      renameMut.mutate({ conversationId: activeId, courseId, title: t })
    }
    setEditing(false)
  }

  if (editing && activeId !== null) {
    return (
      <div className="flex items-center gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") saveRename()
            if (e.key === "Escape") setEditing(false)
          }}
          placeholder="会话标题"
          className="h-8 flex-1"
          autoFocus
        />
        <Button size="sm" onClick={saveRename} disabled={renameMut.isPending} title="保存">
          <Check className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setEditing(false)} title="取消">
          <X className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Select
        value={activeId?.toString() ?? ""}
        onValueChange={(v) => onSelect(v ? Number(v) : null)}
      >
        <SelectTrigger className="h-8 flex-1">
          <SelectValue placeholder="选择会话…" />
        </SelectTrigger>
        <SelectContent>
          {list.length === 0 ? (
            <div className="px-2 py-1.5 text-xs text-muted-foreground">暂无会话，点 + 新建</div>
          ) : (
            list.map((c) => (
              <SelectItem key={c.id} value={c.id.toString()}>
                {c.title}
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
      <Button
        size="sm"
        variant={activeId === null ? "default" : "outline"}
        onClick={() => onSelect(null)}
        title="新建会话"
      >
        <Plus className="h-4 w-4" />
      </Button>
      {activeId !== null && (
        <>
          <Button
            size="sm"
            variant="ghost"
            onClick={startRename}
            disabled={renameMut.isPending}
            title="重命名会话"
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={deleteMut.isPending}
            className="text-destructive"
            onClick={() => {
              deleteMut.mutate({ conversationId: activeId, courseId })
              onSelect(null)
            }}
            title="删除当前会话"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </>
      )}
    </div>
  )
}
