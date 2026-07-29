"use client"

import { useState, useCallback } from "react"
import { Upload, X, Loader2 } from "lucide-react"

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
  isLoading?: boolean
  children?: React.ReactNode
}

export function UploadModal({ onUpload, isLoading, children }: UploadModalProps) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const reset = useCallback(() => {
    setTitle("")
    setFile(null)
  }, [])

  const handleSubmit = async () => {
    if (!file || !title.trim()) return
    const formData = new FormData()
    formData.append("title", title.trim())
    formData.append("file", file)
    await onUpload(formData)
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
          <DialogTitle>上传新课程</DialogTitle>
          <DialogDescription>
            选择视频文件并填写课程标题，系统将自动处理字幕、帧与总结。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="title">课程标题</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如：深度学习入门"
            />
          </div>
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
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)} disabled={isLoading}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={!file || !title.trim() || isLoading}>
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Upload className="mr-2 h-4 w-4" />
            )}
            开始上传
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
