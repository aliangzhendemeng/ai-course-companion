"use client"

import { useState, useCallback } from "react"
import { Upload, X, Loader2, Link2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

interface UploadModalProps {
  onUpload: (formData: FormData) => Promise<void>
  onImport?: (url: string, title?: string) => Promise<void>
  isLoading?: boolean
  isImporting?: boolean
  children?: React.ReactNode
}

export function UploadModal({ onUpload, onImport, isLoading, isImporting, children }: UploadModalProps) {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<"file" | "url">("file")
  const [title, setTitle] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [url, setUrl] = useState("")
  const [dragActive, setDragActive] = useState(false)

  const reset = useCallback(() => {
    setTitle("")
    setFile(null)
    setUrl("")
  }, [])

  const handleSubmitFile = async () => {
    if (!file || !title.trim()) return
    const formData = new FormData()
    formData.append("title", title.trim())
    formData.append("file", file)
    await onUpload(formData)
    reset()
    setOpen(false)
  }

  const handleSubmitImport = async () => {
    if (!url.trim() || !onImport) return
    await onImport(url.trim(), title.trim() || undefined)
    reset()
    setOpen(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) setFile(dropped)
  }

  const busy = isLoading || isImporting

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            上传课程
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{mode === "file" ? "上传新课程" : "链接导入课程"}</DialogTitle>
          <DialogDescription>
            {mode === "file"
              ? "选择视频文件，系统将自动处理字幕、帧与总结。"
              : "粘贴视频链接（B站/YouTube 等通用 URL），后台自动下载并处理。"}
          </DialogDescription>
        </DialogHeader>

        {/* 模式切换 */}
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          <button
            onClick={() => setMode("file")}
            className={`flex-1 rounded px-3 py-1.5 text-sm transition-colors ${
              mode === "file" ? "bg-background shadow-sm font-medium" : "text-muted-foreground"
            }`}
          >
            本地文件
          </button>
          <button
            onClick={() => setMode("url")}
            disabled={!onImport}
            className={`flex-1 rounded px-3 py-1.5 text-sm transition-colors ${
              mode === "url" ? "bg-background shadow-sm font-medium" : "text-muted-foreground"
            } disabled:opacity-40`}
          >
            链接导入
          </button>
        </div>

        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="title">课程标题（可选）</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={mode === "url" ? "留空则用视频原标题" : "例如：深度学习入门"}
            />
          </div>

          {mode === "file" ? (
            <div className="grid gap-2">
              <Label>视频文件</Label>
              <div
                onDragEnter={() => setDragActive(true)}
                onDragLeave={() => setDragActive(false)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors ${
                  dragActive ? "border-primary bg-primary/5" : "border-border"
                }`}
              >
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="video-upload"
                />
                <label htmlFor="video-upload" className="cursor-pointer text-center">
                  <Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                  {file ? (
                    <span className="text-sm font-medium">{file.name}</span>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      拖拽视频到此处，或点击选择文件
                    </span>
                  )}
                </label>
              </div>
            </div>
          ) : (
            <div className="grid gap-2">
              <Label htmlFor="url">视频链接</Label>
              <Input
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.bilibili.com/video/... 或 YouTube 链接"
              />
              <p className="text-xs text-muted-foreground">
                支持 yt-dlp 可解析的平台；版权内容仅供个人学习。
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)} disabled={busy}>
            取消
          </Button>
          {mode === "file" ? (
            <Button onClick={handleSubmitFile} disabled={!file || !title.trim() || busy}>
              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
              开始上传
            </Button>
          ) : (
            <Button onClick={handleSubmitImport} disabled={!url.trim() || busy}>
              {isImporting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Link2 className="mr-2 h-4 w-4" />}
              导入并处理
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
