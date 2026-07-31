"use client"

import { useState } from "react"
import { Bookmark, Loader2, Pencil, PlayCircle, Plus, StickyNote, Trash2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useCreateNote,
  useDeleteNote,
  useNotes,
  useUpdateNote,
} from "@/hooks/use-api"
import { useCompanion } from "@/components/companion/CompanionContext"
import { formatTimestamp } from "@/lib/timestamp"
import type { Note } from "@/lib/api"

interface NotesPanelProps {
  courseId: number
  /** 取播放器当前时间（秒），用于打书签/记笔记 */
  getCurrentTime: () => number
  onSeek?: (timestamp: number) => void
}

/** 笔记/书签面板：看视频随手记笔记、打书签，点击跳回对应时间点。 */
export function NotesPanel({ courseId, getCurrentTime, onSeek }: NotesPanelProps) {
  const { data: notes, isLoading } = useNotes(courseId)
  const createMutation = useCreateNote()
  const updateMutation = useUpdateNote()
  const deleteMutation = useDeleteNote()
  const { react } = useCompanion()

  const [draft, setDraft] = useState("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState("")

  const list = notes ?? []
  const bookmarks = list.filter((n) => n.kind === "bookmark")
  const notesOnly = list.filter((n) => n.kind === "note")

  const handleAddNote = () => {
    const content = draft.trim()
    if (!content || createMutation.isPending) return
    const timestamp = Math.floor(getCurrentTime())
    createMutation.mutate(
      { course_id: courseId, kind: "note", content, timestamp },
      {
        onSuccess: () => {
          setDraft("")
          react("happy", undefined, false)
        },
      }
    )
  }

  const handleAddBookmark = () => {
    if (createMutation.isPending) return
    const timestamp = Math.floor(getCurrentTime())
    createMutation.mutate(
      { course_id: courseId, kind: "bookmark", content: "", timestamp },
      { onSuccess: () => react("happy", undefined, false) }
    )
  }

  const startEdit = (note: Note) => {
    setEditingId(note.id)
    setEditDraft(note.content)
  }

  const handleSaveEdit = () => {
    const content = editDraft.trim()
    if (editingId == null || !content || updateMutation.isPending) return
    updateMutation.mutate(
      { noteId: editingId, courseId, content },
      { onSuccess: () => setEditingId(null) }
    )
  }

  return (
    <div className="flex h-full flex-col gap-3">
      {/* 操作区：记笔记 + 打书签 */}
      <div className="space-y-2">
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="在当前时间点记一条笔记..."
          className="min-h-[64px] resize-none"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault()
              handleAddNote()
            }
          }}
        />
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={handleAddNote}
            disabled={!draft.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : (
              <StickyNote className="mr-1 h-4 w-4" />
            )}
            记笔记
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleAddBookmark}
            disabled={createMutation.isPending}
            title="在当前时间点打一个书签"
          >
            <Bookmark className="mr-1 h-4 w-4" />
            打书签
          </Button>
          <span className="ml-auto text-xs text-muted-foreground">
            {notesOnly.length} 笔记 · {bookmarks.length} 书签
          </span>
        </div>
      </div>

      {/* 列表 */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="space-y-2 pr-2">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : list.length === 0 ? (
          <div className="flex h-32 flex-col items-center justify-center gap-1 text-sm text-muted-foreground">
            <StickyNote className="h-6 w-6 opacity-50" />
            还没有笔记，看视频时随手记一条吧
          </div>
        ) : (
          <ul className="space-y-2 pr-2">
            {list.map((note) => (
              <li
                key={note.id}
                className="group rounded-lg border bg-background p-2.5 text-sm"
              >
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSeek?.(note.timestamp)}
                    className="flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-primary hover:bg-accent"
                    title="跳转到此时间点"
                  >
                    <PlayCircle className="h-3 w-3" />
                    {formatTimestamp(note.timestamp)}
                  </button>
                  {note.kind === "bookmark" ? (
                    <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
                      <Bookmark className="h-3 w-3" /> 书签
                    </span>
                  ) : null}
                  <div className="ml-auto flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    {note.kind === "note" && editingId !== note.id && (
                      <button
                        onClick={() => startEdit(note)}
                        className="text-muted-foreground hover:text-primary"
                        title="编辑"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <button
                      onClick={() =>
                        deleteMutation.mutate({ noteId: note.id, courseId })
                      }
                      className="text-muted-foreground hover:text-destructive"
                      title="删除"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {editingId === note.id ? (
                  <div className="mt-2 space-y-2">
                    <Textarea
                      value={editDraft}
                      onChange={(e) => setEditDraft(e.target.value)}
                      className="min-h-[56px] resize-none"
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={handleSaveEdit} disabled={!editDraft.trim() || updateMutation.isPending}>
                        {updateMutation.isPending ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
                        保存
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                        <X className="mr-1 h-3.5 w-3.5" /> 取消
                      </Button>
                    </div>
                  </div>
                ) : note.content ? (
                  <p className="mt-1.5 whitespace-pre-wrap leading-relaxed">{note.content}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </ScrollArea>
    </div>
  )
}
